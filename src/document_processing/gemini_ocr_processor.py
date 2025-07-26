"""
Gemini OCR-based PDF processor for Bengali text extraction.
Uses Gemini 2.5 Pro for OCR with strict rate limiting and Gemini 2.5 Flash for post-processing.
"""

import base64
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import fitz  # PyMuPDF - only for page splitting, not text extraction
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for Gemini API calls with strict limits."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        
        # Rate limits for different models (Free tier)
        self.limits = {
            "gemini-2.5-pro": {
                "rpm": 5,          # 5 requests per minute
                "tpm": 250000,     # 250k tokens per minute  
                "rpd": 100         # 100 requests per day
            },
            "gemini-2.5-flash": {
                "rpm": 10,         # 10 requests per minute
                "tpm": 250000,     # 250k tokens per minute
                "rpd": 250         # 250 requests per day
            }
        }
        
        self.request_times = []
        self.daily_requests = 0
        self.token_count = 0
        self.token_reset_time = time.time()
        
    def wait_if_needed(self, estimated_tokens: int = 0):
        """Wait if rate limits would be exceeded."""
        current_time = time.time()
        
        # Clean old request times (older than 1 minute)
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Reset token count if more than 1 minute passed
        if current_time - self.token_reset_time > 60:
            self.token_count = 0
            self.token_reset_time = current_time
        
        limits = self.limits.get(self.model_name, self.limits["gemini-2.5-flash"])
        
        # Check RPM limit
        if len(self.request_times) >= limits["rpm"]:
            wait_time = 60 - (current_time - self.request_times[0]) + 1
            if wait_time > 0:
                logger.info(f"RPM limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        # Check TPM limit
        if self.token_count + estimated_tokens > limits["tpm"]:
            wait_time = 61 - (current_time - self.token_reset_time)
            if wait_time > 0:
                logger.info(f"TPM limit would be exceeded. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                self.token_count = 0
                self.token_reset_time = time.time()
        
        # Check RPD limit
        if self.daily_requests >= limits["rpd"]:
            logger.error(f"Daily request limit ({limits['rpd']}) reached!")
            raise Exception(f"Daily request limit reached for {self.model_name}")
        
        # Record this request
        self.request_times.append(time.time())
        self.daily_requests += 1
        self.token_count += estimated_tokens

class GeminiOCRProcessor:
    """OCR-based PDF processor using Gemini models."""
    
    def __init__(self, api_key: str):
        """Initialize the OCR processor."""
        genai.configure(api_key=api_key)
        
        # Initialize models with safety settings
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.ocr_model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            safety_settings=safety_settings
        )
        
        self.processing_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", 
            safety_settings=safety_settings
        )
        
        # Rate limiters
        self.ocr_limiter = RateLimiter("gemini-2.5-pro")
        self.processing_limiter = RateLimiter("gemini-2.5-flash")
        
        logger.info("Gemini OCR Processor initialized")
    
    def _pdf_to_images(self, pdf_path: str) -> List[Tuple[int, bytes]]:
        """Convert PDF pages to image bytes."""
        logger.info(f"Converting PDF to images: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Convert to image with high DPI for better OCR
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            images.append((page_num + 1, img_data))
            logger.info(f"Converted page {page_num + 1} to image")
        
        doc.close()
        return images
    
    def _ocr_page(self, page_num: int, image_data: bytes) -> str:
        """OCR a single page using Gemini 2.5 Pro."""
        try:
            # Estimate tokens (rough estimate for rate limiting)
            estimated_tokens = 1000  # Base tokens for image processing
            
            self.ocr_limiter.wait_if_needed(estimated_tokens)
            
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            prompt = """You are an expert OCR system specializing in Bengali text recognition. 
            Please extract ALL text from this image with perfect accuracy. 

            CRITICAL REQUIREMENTS:
            1. Preserve exact Bengali text with proper Unicode characters
            2. Maintain original formatting, spacing, and line breaks
            3. Extract tables in structured format with | separators
            4. Include question numbers, options (ক, খ, গ, ঘ), and all content
            5. Preserve mathematical symbols, punctuation, and special characters
            6. Do not translate or modify any text - extract exactly as shown
            7. If text is unclear, make your best educated guess based on context

            Return only the extracted text, no explanations or metadata."""

            # Create the request
            response = self.ocr_model.generate_content([
                prompt,
                {
                    "mime_type": "image/png",
                    "data": image_b64
                }
            ])
            
            extracted_text = response.text.strip()
            logger.info(f"Successfully OCR'd page {page_num} - {len(extracted_text)} characters")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error OCRing page {page_num}: {str(e)}")
            return f"[OCR Error on page {page_num}: {str(e)}]"
    
    def _process_mcq_mapping(self, full_text: str) -> Dict[str, Any]:
        """Use Gemini 2.5 Flash to map MCQs with answer tables."""
        try:
            # Estimate tokens
            estimated_tokens = len(full_text.split()) * 2  # Rough estimate
            
            self.processing_limiter.wait_if_needed(estimated_tokens)
            
            prompt = """You are analyzing a Bengali HSC textbook. Your task is to:

            1. IDENTIFY MCQ SECTIONS: Find all multiple-choice questions with their options (ক, খ, গ, ঘ)
            2. IDENTIFY ANSWER TABLES: Find answer key tables that map question numbers to correct options
            3. CREATE MAPPINGS: Match each MCQ with its correct answer from the answer table
            4. PRESERVE CONTENT: Keep all original Bengali text exactly as written

            Please analyze the text and return a JSON structure with:
            {
                "mcq_questions": [
                    {
                        "question_number": "1",
                        "question_text": "original Bengali question",
                        "options": {
                            "ক": "option A text",
                            "খ": "option B text", 
                            "গ": "option C text",
                            "ঘ": "option D text"
                        },
                        "correct_answer": "ক",
                        "page_reference": "page number if available"
                    }
                ],
                "answer_tables": [
                    {
                        "table_content": "original answer table text",
                        "mappings": {"1": "ক", "2": "খ", "3": "গ", ...}
                    }
                ],
                "other_content": {
                    "glossary": "glossary sections if found",
                    "essays": "essay questions if found",
                    "general_text": "other educational content"
                }
            }

            IMPORTANT: Keep all Bengali text in proper Unicode. Do not translate or modify content."""

            response = self.processing_model.generate_content(prompt + "\n\nText to analyze:\n" + full_text)
            
            # Try to parse JSON response
            try:
                result = json.loads(response.text)
                logger.info("Successfully processed MCQ mapping")
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured text
                logger.warning("Could not parse JSON response, returning raw structured content")
                return {
                    "mcq_questions": [],
                    "answer_tables": [],
                    "other_content": {
                        "general_text": response.text
                    },
                    "processing_note": "Could not parse structured format, content preserved as text"
                }
                
        except Exception as e:
            logger.error(f"Error processing MCQ mapping: {str(e)}")
            return {
                "mcq_questions": [],
                "answer_tables": [],
                "other_content": {
                    "general_text": full_text
                },
                "error": str(e)
            }
    
    def _expand_abbreviations(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Use Gemini 2.5 Flash to expand Bengali university and board abbreviations."""
        try:
            estimated_tokens = 500  # Small task
            self.processing_limiter.wait_if_needed(estimated_tokens)
            
            # University and board mappings from guidelines
            abbreviation_mappings = """
            UNIVERSITY ABBREVIATIONS:
            ঢাবি = ঢাকা বিশ্ববিদ্যালয় (University of Dhaka)
            রাবি = রাজশাহী বিশ্ববিদ্যালয় (University of Rajshahi)  
            চবি = চট্টগ্রাম বিশ্ববিদ্যালয় (University of Chittagong)
            জাবি = জাহাঙ্গীরনগর বিশ্ববিদ্যালয় (Jahangirnagar University)
            কুবি = কুমিল্লা বিশ্ববিদ্যালয় (Comilla University)
            বুয়েট = বাংলাদেশ প্রকৌশল ও প্রযুক্তি বিশ্ববিদ্যালয় (BUET)
            
            BOARD ABBREVIATIONS:
            ঢা. বো. = ঢাকা শিক্ষা বোর্ড (Dhaka Education Board)
            রাজশাহী বো. = রাজশাহী শিক্ষা বোর্ড (Rajshahi Education Board)
            চট্টগ্রাম বো. = চট্টগ্রাম শিক্ষা বোর্ড (Chittagong Education Board)
            যশোর বো. = যশোর শিক্ষা বোর্ড (Jessore Education Board)
            """
            
            prompt = f"""Please expand any Bengali university and board abbreviations found in this content using these mappings:

            {abbreviation_mappings}

            Find abbreviations like "জা.বি.", "ঢা. বো.", etc. and expand them to full names.
            Preserve all other content exactly as is.
            Return the content with abbreviations expanded."""

            # Process the content text
            content_text = json.dumps(content, ensure_ascii=False)
            
            response = self.processing_model.generate_content(prompt + "\n\nContent:\n" + content_text)
            
            # Try to parse back to JSON
            try:
                expanded_content = json.loads(response.text)
                logger.info("Successfully expanded abbreviations")
                return expanded_content
            except:
                # If parsing fails, return original with note
                content["abbreviation_expansion_note"] = "Processed but could not parse structured response"
                return content
                
        except Exception as e:
            logger.error(f"Error expanding abbreviations: {str(e)}")
            content["abbreviation_error"] = str(e)
            return content
    
    def process_pdf(self, pdf_path: str, output_dir: str = "processed_documents") -> Dict[str, Any]:
        """Main method to process PDF using OCR and post-processing."""
        start_time = time.time()
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        logger.info(f"Starting OCR processing of {pdf_path}")
        
        # Step 1: Convert PDF to images
        images = self._pdf_to_images(pdf_path)
        
        # Step 2: OCR each page with Gemini 2.5 Pro
        all_text = []
        for page_num, image_data in images:
            logger.info(f"OCRing page {page_num}/{len(images)}")
            page_text = self._ocr_page(page_num, image_data)
            all_text.append(f"\n--- PAGE {page_num} ---\n{page_text}")
        
        full_text = "\n".join(all_text)
        
        # Save raw OCR output
        raw_output_path = Path(output_dir) / "raw_ocr_output.txt"
        with open(raw_output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        logger.info(f"Raw OCR saved to {raw_output_path}")
        
        # Step 3: Process MCQ mapping with Gemini 2.5 Flash
        logger.info("Processing MCQ mapping and structure...")
        structured_content = self._process_mcq_mapping(full_text)
        
        # Step 4: Expand abbreviations
        logger.info("Expanding abbreviations...")
        final_content = self._expand_abbreviations(structured_content)
        
        # Add metadata
        final_content["processing_metadata"] = {
            "total_pages": len(images),
            "processing_time_seconds": time.time() - start_time,
            "total_characters": len(full_text),
            "models_used": ["gemini-2.5-pro", "gemini-2.5-flash"],
            "source_file": pdf_path
        }
        
        # Save structured output
        structured_output_path = Path(output_dir) / "structured_content.json"
        with open(structured_output_path, 'w', encoding='utf-8') as f:
            json.dump(final_content, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Structured content saved to {structured_output_path}")
        
        # Save human-readable format
        readable_output_path = Path(output_dir) / "readable_content.txt"
        self._save_readable_format(final_content, readable_output_path)
        
        processing_time = time.time() - start_time
        logger.info(f"Processing completed in {processing_time:.2f} seconds")
        
        return final_content
    
    def _save_readable_format(self, content: Dict[str, Any], output_path: Path):
        """Save content in human-readable format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# OCR PROCESSED BENGALI TEXTBOOK CONTENT\n\n")
            
            # MCQ Questions
            if content.get("mcq_questions"):
                f.write("## MCQ QUESTIONS\n\n")
                for mcq in content["mcq_questions"]:
                    f.write(f"**Question {mcq.get('question_number', 'N/A')}:**\n")
                    f.write(f"{mcq.get('question_text', '')}\n\n")
                    
                    options = mcq.get('options', {})
                    for key, value in options.items():
                        f.write(f"{key}) {value}\n")
                    
                    f.write(f"**Correct Answer:** {mcq.get('correct_answer', 'N/A')}\n\n")
                    f.write("---\n\n")
            
            # Answer Tables
            if content.get("answer_tables"):
                f.write("## ANSWER TABLES\n\n")
                for table in content["answer_tables"]:
                    f.write(f"{table.get('table_content', '')}\n\n")
                    f.write("---\n\n")
            
            # Other Content
            other = content.get("other_content", {})
            if other.get("glossary"):
                f.write("## GLOSSARY\n\n")
                f.write(f"{other['glossary']}\n\n")
            
            if other.get("essays"):
                f.write("## ESSAY QUESTIONS\n\n")
                f.write(f"{other['essays']}\n\n")
            
            if other.get("general_text"):
                f.write("## GENERAL CONTENT\n\n")
                f.write(f"{other['general_text']}\n\n")
            
            # Metadata
            metadata = content.get("processing_metadata", {})
            f.write("## PROCESSING INFORMATION\n\n")
            for key, value in metadata.items():
                f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    
    processor = GeminiOCRProcessor(api_key)
    
    # Process the HSC PDF
    pdf_path = "data/HSC26-Bangla1st-Paper.pdf"
    result = processor.process_pdf(pdf_path)
    
    print(f"Processing complete! Results saved in 'processed_documents' directory.")
