#!/usr/bin/env python3
"""
Simple Document Separator using Gemini 2.5 Flash
Separates the raw OCR content into 4 distinct files as requested
"""

import os
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleDocumentSeparator:
    def __init__(self):
        """Initialize with Gemini 2.5 Flash"""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 6.5
    
    def _rate_limit(self):
        """Ensure rate limiting compliance"""
        current_time = time.time()
        if current_time - self.last_request_time < self.min_request_interval:
            sleep_time = self.min_request_interval - (current_time - self.last_request_time)
            print(f"Rate limiting: sleeping for {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _call_gemini(self, prompt: str) -> str:
        """Make a rate-limited call to Gemini"""
        try:
            self._rate_limit()
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return ""
    
    def create_table_content(self, raw_content: str, abbreviations: str) -> str:
        """Extract table content"""
        print("Creating table content file...")
        
        prompt = f"""
        Extract ALL table content from this Bengali HSC textbook. Look for:
        1. Glossary tables (শব্দার্থ ও টীকা)
        2. Any other tabular data with columns
        3. Word definitions and explanations
        
        For each table entry, format as:
        শব্দ/বাক্য: [original word/phrase]
        অর্থ ও ব্যাখ্যা: [meaning and explanation]
        
        Use these abbreviations to expand any short forms:
        {abbreviations}
        
        Raw OCR Content:
        {raw_content}
        
        Extract and format all table content properly. Return only the table content, nothing else.
        """
        
        return self._call_gemini(prompt)
    
    def create_mcq_content(self, raw_content: str, abbreviations: str) -> str:
        """Extract MCQ content with answers"""
        print("Creating MCQ content file...")
        
        prompt = f"""
        Extract ALL MCQ (Multiple Choice Questions) from this Bengali HSC textbook. Look for:
        1. Questions with options ক, খ, গ, ঘ
        2. Their correct answers
        3. Any exam references or citations
        4. Explanation of the questions if provided

        For each MCQ, format as:
        প্রশ্ন [number]: [question text]
        ক) [option A]
        খ) [option B] 
        গ) [option C]
        ঘ) [option D]
        সঠিক উত্তর: [correct answer]
        [Explanation of the questions if provided]
        [exam reference if any]
        
        IMPORTANT: Expand all abbreviations using this list:
        {abbreviations}
        
        For example: ঢা.বি. → ঢাকা বিশ্ববিদ্যালয়, ঢা.বো. → ঢাকা শিক্ষা বোর্ড
        
        Raw OCR Content:
        {raw_content}
        
        Extract all MCQs with their answers and expand abbreviations. Return only MCQ content.
        """
        
        return self._call_gemini(prompt)
    
    def create_creative_questions(self, raw_content: str, abbreviations: str) -> str:
        """Extract creative/essay questions (সৃজনশীল প্রশ্ন)"""
        print("Creating creative questions file...")
        
        prompt = f"""
        Extract ALL creative questions (সৃজনশীল প্রশ্ন) and essay-style questions from this Bengali HSC textbook. Look for:
        1. Long-form questions requiring detailed answers
        2. Questions asking for explanations, analysis, or interpretation
        3. Questions with passages or contexts
        4. Any creative or analytical questions
        
        Format each question clearly with:
        - Question number
        - Full question text
        - Any context or passage provided
        - Any exam references
        
        IMPORTANT: Expand all abbreviations using this list:
        {abbreviations}
        
        For example: জা.বি. → জাহাঙ্গীরনগর বিশ্ববিদ্যালয়
        
        Raw OCR Content:
        {raw_content}
        
        Extract all creative/essay questions and expand abbreviations. Return only creative question content.
        """
        
        return self._call_gemini(prompt)
    
    def create_rest_content(self, raw_content: str, abbreviations: str) -> str:
        """Extract remaining content"""
        print("Creating rest of content file...")
        
        prompt = f"""
        Extract all OTHER content from this Bengali HSC textbook that is NOT:
        - Tables/glossary entries
        - MCQ questions
        - Creative/essay questions
        
        This should include:
        1. Story text and narratives
        2. Learning objectives (শিখনফল)
        3. General explanatory text
        4. Any other educational content
        
        IMPORTANT: Expand all abbreviations using this list:
        {abbreviations}
        
        Raw OCR Content:
        {raw_content}
        
        Extract all remaining content and expand abbreviations. Return only the rest of the content.
        """
        
        return self._call_gemini(prompt)
    
    def process_document(self):
        """Main processing function"""
        print("Starting document separation process...")
        
        # Read raw OCR content
        raw_file = "processed_documents/raw_ocr_output.txt"
        if not Path(raw_file).exists():
            print(f"Error: {raw_file} not found!")
            return
        
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        print(f"Loaded {len(raw_content):,} characters from raw OCR")
        
        # Read abbreviations
        abbrev_file = "Abbreviations.md"
        if not Path(abbrev_file).exists():
            print(f"Error: {abbrev_file} not found!")
            return
        
        with open(abbrev_file, 'r', encoding='utf-8') as f:
            abbreviations = f.read()
        
        print(f"Loaded abbreviations file")
        
        # Create output directory
        output_dir = Path("processed_documents/separated_content")
        output_dir.mkdir(exist_ok=True)
        
        # Create 4 separate files
        files_to_create = [
            ("table_content.txt", self.create_table_content),
            ("mcq_content.txt", self.create_mcq_content), 
            ("creative_questions.txt", self.create_creative_questions),
            ("rest_content.txt", self.create_rest_content)
        ]
        
        for filename, extraction_func in files_to_create:
            print(f"\n{'='*50}")
            print(f"Processing: {filename}")
            print('='*50)
            
            content = extraction_func(raw_content, abbreviations)
            
            if content:
                output_file = output_dir / filename
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Created: {output_file}")
                print(f"   Length: {len(content):,} characters")
            else:
                print(f"❌ Failed to create: {filename}")
        
        print(f"\n🎯 Document separation complete!")
        print(f"📁 Output directory: {output_dir}")

def main():
    separator = SimpleDocumentSeparator()
    separator.process_document()

if __name__ == "__main__":
    main()
