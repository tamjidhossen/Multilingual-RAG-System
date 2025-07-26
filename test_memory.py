#!/usr/bin/env python3
"""
Test script to demonstrate memory functionality in the RAG system
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.pipeline import RAGPipeline
from src.memory.memory_manager import get_memory_manager


def test_memory_functionality():
    """Test the memory functionality with various queries"""
    print("🧠 Testing RAG System Memory Functionality")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = RAGPipeline()
    memory_manager = get_memory_manager()
    
    # Create a new session
    session_id = memory_manager.create_session()
    print(f"📝 Created new session: {session_id}")
    print()
    
    # Test queries
    test_queries = [
        "অনুপমের বাবা কী করে জীবিকা নির্বাহ করতেন?",  # First regular query
        "কাকে অনুপমের ভাগ্য দেবতা বলে উল্লেখ করা হয়েছে?",  # Second regular query
        "আমার শেষ প্রশ্ন কী ছিল?",  # Memory query in Bengali
        "what was my last query?",  # Memory query in English
        "আগের উত্তরটা কী ছিল?",  # Another memory query in Bengali
        "tell me about my previous question"  # Another memory query in English
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Query {i}: {query}")
        print("-" * 30)
        
        try:
            response = pipeline.process_query(query, session_id=session_id)
            
            print(f"🌐 Language: {response['language']}")
            print(f"💬 Answer: {response['answer']}")
            print(f"🎯 Confidence: {response.get('confidence', 0):.2f}")
            print(f"📚 Context Used: {response.get('context_used', 0)}")
            
            if response.get('memory_query'):
                print("🧠 Memory Query: YES")
            
            if response.get('sources'):
                print(f"📄 Sources: {len(response['sources'])}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
        print("─" * 50)
        print()
    
    # Show session statistics
    print("📊 Session Statistics:")
    session_stats = memory_manager.get_session_stats(session_id)
    if session_stats:
        print(f"   Messages: {session_stats['message_count']}")
        print(f"   Languages: {session_stats['languages_used']}")
        print(f"   Avg Confidence: {session_stats['avg_confidence']:.2f}")
    
    print()
    print("🗂️ Chat History:")
    history = memory_manager.get_session_history(session_id)
    for i, msg in enumerate(history, 1):
        print(f"   {i}. Q: {msg.query}")
        print(f"      A: {msg.response[:100]}...")
        print()


if __name__ == "__main__":
    test_memory_functionality()
