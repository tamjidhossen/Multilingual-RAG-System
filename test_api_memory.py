#!/usr/bin/env python3
"""
Test API memory functionality
"""
import requests
import json

def test_api_memory():
    base_url = "http://localhost:8000"
    
    # First query
    response1 = requests.post(f"{base_url}/query", json={
        "query": "অনুপমের বাবা কী করতেন?"
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        session_id = data1.get('session_id')
        print(f"✅ First query successful")
        print(f"Session ID: {session_id}")
        print(f"Answer: {data1['answer']}")
        print()
        
        # Memory query
        response2 = requests.post(f"{base_url}/query", json={
            "query": "আমার শেষ প্রশ্ন কী ছিল?",
            "session_id": session_id
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"✅ Memory query successful")
            print(f"Answer: {data2['answer']}")
            print(f"Confidence: {data2['confidence']}")
            
            # English memory query
            response3 = requests.post(f"{base_url}/query", json={
                "query": "what was my last query?",
                "session_id": session_id
            })
            
            if response3.status_code == 200:
                data3 = response3.json()
                print(f"✅ English memory query successful")
                print(f"Answer: {data3['answer']}")
                print(f"Confidence: {data3['confidence']}")
            else:
                print(f"❌ English memory query failed: {response3.status_code}")
        else:
            print(f"❌ Memory query failed: {response2.status_code}")
    else:
        print(f"❌ First query failed: {response1.status_code}")

if __name__ == "__main__":
    test_api_memory()
