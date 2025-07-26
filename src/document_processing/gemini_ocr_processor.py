"""
Gemini OCR-based PDF processor for Bengali text extraction.
Uses Gemini 2.5 Pro for high-quality OCR with strict rate limiting.
"""

import base64
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import fitz  # PyMuPDF - only for page splitting, not text extraction
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for Gemini API calls with strict limits."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        
        # Rate limits for Gemini 2.5 Pro (Free tier)
        self.limits = {
            "gemini-2.5-pro": {
                "rpm": 5,          # 5 requests per minute
                "tpm": 250000,     # 250k tokens per minute  
                "rpd": 100         # 100 requests per day
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
        
        limits = self.limits.get(self.model_name, self.limits["gemini-2.5-pro"])
        
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
        
        # Initialize OCR model with safety settings
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
        
        # Rate limiter for OCR model
        self.ocr_limiter = RateLimiter("gemini-2.5-pro")
        
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
    


    
    def process_pdf(self, pdf_path: str, output_dir: str = "processed_documents") -> Dict[str, Any]:
        """Main method to process PDF using OCR - simplified to only generate raw OCR output."""
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
        
        # Prepare return metadata
        processing_metadata = {
            "total_pages": len(images),
            "processing_time_seconds": time.time() - start_time,
            "total_characters": len(full_text),
            "models_used": ["gemini-2.5-pro"],
            "source_file": pdf_path,
            "output_file": str(raw_output_path)
        }
        
        processing_time = time.time() - start_time
        logger.info(f"OCR processing completed in {processing_time:.2f} seconds")
        
        return {
            "raw_text": full_text,
            "processing_metadata": processing_metadata
        }



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
    
    print(f"OCR processing complete! Raw text saved to: {result['processing_metadata']['output_file']}")
    print(f"Total characters extracted: {result['processing_metadata']['total_characters']:,}")
    print(f"Total pages processed: {result['processing_metadata']['total_pages']}")
    print(f"Processing time: {result['processing_metadata']['processing_time_seconds']:.2f} seconds")
