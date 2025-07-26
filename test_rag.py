#!/usr/bin/env python3
"""
Simple RAG system test script for production use
"""
import os
import sys
import time

# Add project root to path
project_root = "/home/tamjid/Codes/Projects/Multilingual_RAG_SYSTEM_10MS"
sys.path.insert(0, project_root)

from src.rag.pipeline import RAGPipeline


def main():
    """Test the RAG system with sample queries"""
    print("🤖 MULTILINGUAL RAG SYSTEM TEST")
    print("=" * 50)
    
    try:
        print("🔧 Initializing RAG Pipeline...")
        pipeline = RAGPipeline()
        print("✅ Pipeline ready!")
        
        # Test queries from project requirements
        test_queries = [
            "অনুপমের বাবা কী করে জীবিকা নির্বাহ করতেন?",
            "কাকে অনুপমের ভাগ্য দেবতা বলে উল্লেখ করা হয়েছে?", 
            "বিয়ের সময় কল্যাণীর প্রকৃত বয়স কত ছিল?",
            "Who is referred to as 'সুপুরুষ' in Anupam's language?",
            "What was Kalyani's actual age at marriage?"
        ]
        
        print(f"\n🧪 Testing with {len(test_queries)} queries...")
        print("=" * 50)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}: {query}")
            print("-" * 40)
            
            start_time = time.time()
            
            try:
                response = pipeline.process_query(query)
                end_time = time.time()
                
                print(f"⚡ Response Time: {end_time - start_time:.2f}s")
                print(f"🌐 Language: {response['language']}")
                print(f"📄 Chunks Used: {response['context_used']}")
                print(f"🎯 Confidence: {response['confidence']:.3f}")
                print(f"💬 Answer: {response['answer']}")
                
                if response.get('error'):
                    print(f"⚠️  Warning: {response['error']}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "🏆 RAG SYSTEM TEST COMPLETED!")
        
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        print("💡 Make sure you've run 'python build_index.py' first")


if __name__ == "__main__":
    main()
