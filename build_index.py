#!/usr/bin/env python3
"""
One-time indexer for production knowledge base
Run this once to build the complete index with rate limiting
"""
import os
import sys
import time
from datetime import datetime

# Add project root to path
project_root = "/home/tamjid/Codes/Projects/Multilingual_RAG_SYSTEM_10MS"
sys.path.insert(0, project_root)

from src.knowledge_base.indexer import KnowledgeBaseIndexer


def main():
    """One-time production indexing with proper rate limiting"""
    print("🏗️  PRODUCTION KNOWLEDGE BASE INDEXER")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⏱️  Rate Limiting: ENABLED (prevents API quota exhaustion)")
    print("🔄 Retry Logic: ENABLED (handles temporary API issues)")
    print("📊 Progress Updates: Every 25 embeddings")
    print("=" * 60)
    
    try:
        start_time = time.time()
        
        print("\n🔧 Initializing indexer...")
        indexer = KnowledgeBaseIndexer()
        
        base_path = "/home/tamjid/Codes/Projects/Multilingual_RAG_SYSTEM_10MS/processed_documents"
        
        print("📁 Processing separated content files:")
        print("   ✓ mcq_content.txt")
        print("   ✓ creative_questions.txt") 
        print("   ✓ table_content.txt")
        print("   ✓ rest_content.txt")
        print()
        
        print("🚀 Starting indexing process...")
        print("⚠️  This may take 5-10 minutes due to rate limiting")
        print("💡 Grab a coffee while the embeddings are generated!")
        print("-" * 60)
        
        # Build the index
        indexer.rebuild_index(base_path)
        
        # Get final statistics
        stats = indexer.get_index_stats()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "🎉 INDEXING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"⏱️  Total Time: {total_time/60:.1f} minutes ({total_time:.1f} seconds)")
        print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📊 Final Knowledge Base Statistics:")
        print("-" * 40)
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Knowledge base is ready for queries!")
        print("🎯 Next steps:")
        print("   • Run 'python -m src.rag.pipeline' to test queries")
        print("   • Use smart_chunk_viewer.py to analyze chunks")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Indexing interrupted by user")
        print("💡 You can resume by running this script again")
        return False
        
    except Exception as e:
        print(f"\n❌ Indexing failed: {e}")
        print("💡 Check your API key and internet connection")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🏁 Production indexing completed successfully!")
    else:
        print("\n❌ Indexing incomplete. Please check errors above.")
