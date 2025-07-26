#!/usr/bin/env python3
"""
Test script for Gemini OCR processor.
This will process the HSC PDF using OCR and save the results.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from document_processing.gemini_ocr_processor import GeminiOCRProcessor

def main():
    """Main function to test OCR processing."""
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable is required")
        print("Please add your Gemini API key to the .env file")
        return
    
    # Check if PDF exists
    pdf_path = "data/HSC26-Bangla1st-Paper.pdf"
    if not Path(pdf_path).exists():
        print(f"❌ Error: PDF file not found at {pdf_path}")
        return
    
    print("🚀 Starting Gemini OCR processing...")
    print(f"📄 Processing: {pdf_path}")
    print("⚠️  Note: This will use Gemini 2.5 Pro (strict rate limits) and may take time")
    print("⏰ Expected processing time: 20-30 minutes for full document")
    print()
    
    # Initialize processor
    try:
        processor = GeminiOCRProcessor(api_key)
        print("✅ Gemini OCR Processor initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing processor: {e}")
        return
    
    # Process the PDF
    try:
        result = processor.process_pdf(pdf_path)
        
        print("\n🎉 Processing completed successfully!")
        print(f"📊 Processed {result['processing_metadata']['total_pages']} pages")
        print(f"⏱️  Total time: {result['processing_metadata']['processing_time_seconds']:.2f} seconds")
        print(f"📝 Total characters: {result['processing_metadata']['total_characters']:,}")
        print()
        print("📁 Output files saved in 'processed_documents' directory:")
        print("   - raw_ocr_output.txt (raw OCR text)")
        print("   - structured_content.json (structured JSON)")
        print("   - readable_content.txt (human-readable format)")
        
        # Show a sample of MCQ questions if found
        mcq_count = len(result.get('mcq_questions', []))
        if mcq_count > 0:
            print(f"\n🧠 Found {mcq_count} MCQ questions")
            print("Sample MCQ:")
            sample_mcq = result['mcq_questions'][0]
            print(f"   Q{sample_mcq.get('question_number', 'N/A')}: {sample_mcq.get('question_text', '')[:100]}...")
        
        answer_tables = len(result.get('answer_tables', []))
        if answer_tables > 0:
            print(f"📋 Found {answer_tables} answer table(s)")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        print("This might be due to:")
        print("   - Rate limit exceeded (wait and try again)")
        print("   - API key issues")
        print("   - Network connectivity problems")

if __name__ == "__main__":
    main()
