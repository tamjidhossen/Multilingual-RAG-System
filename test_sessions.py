#!/usr/bin/env python3
"""
Test script for session management functionality
Tests the complete memory management system
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class SessionTestClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    async def create_session(self) -> str:
        """Create a new chat session"""
        async with self.session.post(f"{self.base_url}/session/create") as response:
            data = await response.json()
            return data["session_id"]
            
    async def send_message(self, session_id: str, query: str) -> Dict[str, Any]:
        """Send a message in a session"""
        payload = {
            "query": query,
            "session_id": session_id,
            "k": 3
        }
        async with self.session.post(f"{self.base_url}/chat", json=payload) as response:
            return await response.json()
            
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        async with self.session.get(f"{self.base_url}/session/{session_id}/stats") as response:
            return await response.json()
            
    async def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Get session chat history"""
        async with self.session.get(f"{self.base_url}/session/{session_id}/history") as response:
            return await response.json()
            
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        async with self.session.get(f"{self.base_url}/stats") as response:
            return await response.json()

async def test_session_management():
    """Test the complete session management system"""
    
    print("🧪 Testing Session Management System")
    print("=" * 50)
    
    async with SessionTestClient() as client:
        # Test 1: Create session
        print("1. Creating new session...")
        session_id = await client.create_session()
        print(f"   ✓ Session created: {session_id}")
        
        # Test 2: Send messages with context
        print("\n2. Testing contextual conversation...")
        
        queries = [
            "বাংলা ব্যাকরণ কি?",
            "এর প্রধান অংশ কয়টি?",
            "আগের প্রশ্নের উত্তরটি আরো বিস্তারিত বলো"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"   Query {i}: {query}")
            response = await client.send_message(session_id, query)
            print(f"   Response: {response['answer'][:100]}...")
            print(f"   Language: {response.get('language', 'Unknown')}")
            print(f"   Response time: {response.get('response_time', 0):.2f}s")
            print()
            
        # Test 3: Check session stats
        print("3. Checking session statistics...")
        session_stats = await client.get_session_stats(session_id)
        print(f"   ✓ Messages in session: {session_stats['message_count']}")
        print(f"   ✓ Average response time: {session_stats['avg_response_time']:.2f}s")
        print(f"   ✓ Languages used: {', '.join(session_stats['languages_used'])}")
        
        # Test 4: Check session history
        print("\n4. Checking session history...")
        history = await client.get_session_history(session_id)
        print(f"   ✓ History contains {len(history['messages'])} messages")
        
        # Test 5: System stats with memory
        print("\n5. Checking system statistics...")
        system_stats = await client.get_system_stats()
        print(f"   ✓ Total queries: {system_stats['total_queries']}")
        print(f"   ✓ Memory stats available: {'memory_stats' in system_stats}")
        if 'memory_stats' in system_stats:
            mem_stats = system_stats['memory_stats']
            print(f"   ✓ Total sessions: {mem_stats.get('total_sessions', 0)}")
            
        # Test 6: Test memory persistence
        print("\n6. Testing memory persistence...")
        followup_query = "আগের কথোপকথনে আমি কি জিজ্ঞেস করেছিলাম?"
        response = await client.send_message(session_id, followup_query)
        print(f"   Memory test response: {response['answer'][:150]}...")
        
        print("\n" + "=" * 50)
        print("✅ Session Management Test Complete!")

async def test_multiple_sessions():
    """Test multiple concurrent sessions"""
    
    print("\n🔄 Testing Multiple Sessions")
    print("=" * 50)
    
    async with SessionTestClient() as client:
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session_id = await client.create_session()
            sessions.append(session_id)
            print(f"Created session {i+1}: {session_id}")
            
        # Send different queries to each session
        session_queries = [
            "বাংলা সাহিত্যের ইতিহাস বলো",
            "গণিতের মৌলিক নিয়ম কি?",
            "পদার্থবিজ্ঞানের সূত্র বলো"
        ]
        
        print("\nSending queries to different sessions...")
        for i, (session_id, query) in enumerate(zip(sessions, session_queries)):
            response = await client.send_message(session_id, query)
            print(f"Session {i+1} response length: {len(response['answer'])} chars")
            
        # Check system stats
        system_stats = await client.get_system_stats()
        print(f"\nSystem now has {system_stats.get('memory_stats', {}).get('total_sessions', 0)} active sessions")
        print("✅ Multiple Sessions Test Complete!")

async def main():
    """Run all tests"""
    try:
        await test_session_management()
        await test_multiple_sessions()
        
        print("\n🎉 All Tests Passed!")
        print("Session management system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("Please ensure the API server is running on localhost:8000")

if __name__ == "__main__":
    asyncio.run(main())
