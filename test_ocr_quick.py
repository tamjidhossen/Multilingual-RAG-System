#!/usr/bin/env python3
"""
Quick test of the OCR processor with rate limit awareness.
Tests first few pages only to validate the system.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from document_processing.gemini_ocr_processor import GeminiOCRProcessor

def main():
    """Test OCR with first 2 pages only."""
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable is required")
        return
    
    pdf_path = "data/HSC26-Bangla1st-Paper.pdf"
    if not Path(pdf_path).exists():
        print(f"❌ Error: PDF file not found at {pdf_path}")
        return
    
    print("🧪 Testing Gemini OCR with first 2 pages...")
    print("⚠️  This is a limited test to validate the system")
    print()
    
    try:
        # Initialize processor
        from document_processing.gemini_ocr_processor import GeminiOCRProcessor
        processor = GeminiOCRProcessor(api_key)
        
        # Convert only first 2 pages to test
        import fitz
        doc = fitz.open(pdf_path)
        
        print(f"📄 PDF has {len(doc)} total pages")
        print("🔍 Processing first 2 pages for testing...")
        
        # Test with first 2 pages only
        images = []
        for page_num in range(min(2, len(doc))):
            page = doc.load_page(page_num)
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            images.append((page_num + 1, img_data))
        
        doc.close()
        
        # OCR the pages
        all_text = []
        for page_num, image_data in images:
            print(f"🔍 OCRing page {page_num}...")
            page_text = processor._ocr_page(page_num, image_data)
            all_text.append(f"\n--- PAGE {page_num} ---\n{page_text}")
            print(f"✅ Page {page_num}: {len(page_text)} characters extracted")
            
            # Check if Bengali text is properly extracted
            bengali_range = '\u0980\u09FF'
            bengali_chars = len([c for c in page_text if '\u0980' <= c <= '\u09FF'])
            print(f"   📝 Bengali characters: {bengali_chars}")
            print(f"   🔤 Sample text: {page_text[:100].strip()}...")
            print()
        
        full_text = "\n".join(all_text)
        
        # Save test output
        test_output_dir = Path("test_ocr_output")
        test_output_dir.mkdir(exist_ok=True)
        
        with open(test_output_dir / "test_pages.txt", 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"✅ Test completed! Output saved to {test_output_dir}/test_pages.txt")
        print(f"📊 Total characters extracted: {len(full_text):,}")
        
        bengali_total = len([c for c in full_text if '\u0980' <= c <= '\u09FF'])
        print(f"🔤 Bengali characters: {bengali_total:,}")
        
        # Test if the text looks correct
        if len(full_text) > 100 and any('\u0980' <= c <= '\u09FF' for c in full_text):
            print("🎉 Bengali text extraction appears successful!")
            print("💡 Ready to process full document when needed")
        else:
            print("⚠️  Warning: Limited Bengali text detected. Check output file.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your API key and internet connection")

if __name__ == "__main__":
    main()
