# Session Management API Reference

## Overview
Session management enables persistent conversation tracking and memory-aware interactions in the Multilingual RAG System.

## API Endpoints

### Create Session
```bash
POST /session/create
```

**Response:**
```json
{
    "session_id": "session_1753550133_696",
    "created": true
}
```

### Query with Session
```bash
POST /query
```

**Request:**
```json
{
    "query": "অনুপমের বাবা কী করতেন?",
    "session_id": "session_1753550133_696",
    "k": 5
}
```

**Response:**
```json
{
    "query": "অনুপমের বাবা কী করতেন?",
    "answer": "অনুপমের বাবা ওকালতি করতেন।",
    "language": "bn",
    "confidence": 0.85,
    "context_used": 3,
    "sources": ["doc_1", "doc_2"],
    "response_time": 2.34,
    "session_id": "session_1753550133_696",
    "pipeline_info": {
        "query_processed": true,
        "documents_retrieved": 3,
        "query_language": "bn",
        "query_type": "factual",
        "session_id": "session_1753550133_696",
        "chat_context_used": false
    }
}
```

### Memory Query Example
```bash
POST /query
```

**Request:**
```json
{
    "query": "আমার শেষ প্রশ্ন কী ছিল?",
    "session_id": "session_1753550133_696"
}
```

**Response:**
```json
{
    "query": "আমার শেষ প্রশ্ন কী ছিল?",
    "answer": "আপনার শেষ প্রশ্ন ছিল: \"অনুপমের বাবা কী করতেন?\"",
    "language": "bn",
    "confidence": 1.0,
    "context_used": 0,
    "sources": [],
    "memory_query": true,
    "session_id": "session_1753550133_696"
}
```

### Get Session Statistics
```bash
GET /session/{session_id}/stats
```

**Response:**
```json
{
    "session_id": "session_1753550133_696",
    "message_count": 5,
    "languages_used": ["bn", "en"],
    "avg_confidence": 0.87,
    "created_at": 1753550133.264,
    "last_activity": 1753550200.123,
    "duration": 66.859
}
```

### Get Session History
```bash
GET /session/{session_id}/history?limit=10
```

**Response:**
```json
{
    "session_id": "session_1753550133_696",
    "messages": [
        {
            "timestamp": 1753550140.123,
            "query": "অনুপমের বাবা কী করতেন?",
            "response": "অনুপমের বাবা ওকালতি করতেন।",
            "language": "bn",
            "confidence": 0.85,
            "sources_used": ["doc_1", "doc_2"]
        }
    ],
    "total_messages": 1
}
```

## Memory Query Patterns

### Bengali Memory Queries
- `আমার শেষ প্রশ্ন কী ছিল?` - "What was my last question?"
- `আগের উত্তর কী ছিল?` - "What was the previous answer?"
- `আমার পূর্বের প্রশ্ন` - "My previous question"

### English Memory Queries
- `what was my last query?`
- `my previous question`
- `what did you say before?`
- `tell me about my last question`

## Usage Examples

### Python Client
```python
import requests

# Create session
response = requests.post("http://localhost:8000/session/create")
session_id = response.json()["session_id"]

# Query with memory
data = {
    "query": "অনুপমের বাবা কী করতেন?",
    "session_id": session_id
}
response = requests.post("http://localhost:8000/query", json=data)

# Memory query
memory_data = {
    "query": "আমার শেষ প্রশ্ন কী ছিল?",
    "session_id": session_id
}
memory_response = requests.post("http://localhost:8000/query", json=memory_data)
```

### curl Examples
```bash
# Create session
SESSION_ID=$(curl -s -X POST "http://localhost:8000/session/create" | jq -r '.session_id')

# Regular query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"অনুপমের বাবা কী করতেন?\", \"session_id\": \"$SESSION_ID\"}"

# Memory query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"what was my last query?\", \"session_id\": \"$SESSION_ID\"}"
```

For detailed memory system documentation, see [MEMORY_SYSTEM.md](MEMORY_SYSTEM.md).
            "assistant_response": "বাংলা ব্যাকরণ হলো...",
            "language": "bengali",
            "timestamp": "2024-01-01T10:15:00Z"
        }
    ]
}
```

### 4. Get Session Details
**GET** `/session/{session_id}`

Retrieves complete session information including stats and recent messages.

**Response:**
```json
{
    "session_id": "sess_1234567890abcdef",
    "stats": {
        "message_count": 5,
        "avg_response_time": 2.34
    },
    "recent_messages": [...],
    "context_summary": "Conversation about Bengali grammar"
}
```

## Enhanced Chat Endpoint

### Chat with Session Support
**POST** `/chat`

The chat endpoint now supports session-based conversations.

**Request:**
```json
{
    "query": "আগের প্রশ্নের উত্তরটি আরো বিস্তারিত বলো",
    "session_id": "sess_1234567890abcdef",
    "k": 5
}
```

**Response:**
```json
{
    "answer": "আগে আমি বাংলা ব্যাকরণ সম্পর্কে বলেছিলাম...",
    "language": "bengali",
    "confidence": 0.95,
    "sources_count": 3,
    "response_time": 2.1,
    "session_id": "sess_1234567890abcdef"
}
```

## System Statistics with Memory

### Enhanced System Stats
**GET** `/stats`

Now includes memory management statistics.

**Response:**
```json
{
    "total_queries": 150,
    "avg_response_time": 2.45,
    "memory_stats": {
        "total_sessions": 12,
        "active_sessions": 8,
        "total_messages": 450,
        "avg_session_length": 6.2
    },
    "system_health": "healthy"
}
```

## Session Management Features

### 1. Context Persistence
- Maintains conversation history across multiple queries
- Enables follow-up questions and contextual responses
- Supports both Bengali and English context retention

### 2. Memory Management
- Automatic session cleanup for inactive sessions
- Configurable memory limits and retention policies
- Efficient storage and retrieval of conversation data

### 3. Language Continuity
- Remembers user's preferred language per session
- Maintains consistent language across conversation
- Supports mixed-language conversations

### 4. Fallback Mechanisms
- Graceful handling of memory retrieval failures
- Fallback to standard RAG when memory is unavailable
- Error recovery and session restoration

## Frontend Integration

### Session Initialization
The web interface automatically creates a session when loaded:

```javascript
async initializeSession() {
    const response = await fetch('/session/create', { method: 'POST' });
    const data = await response.json();
    this.sessionId = data.session_id;
}
```

### Session-Aware Chat
All chat messages include session context:

```javascript
const requestBody = {
    query: message,
    k: 5,
    session_id: this.sessionId
};
```

## Testing Session Management

Use the provided test script to verify session functionality:

```bash
python test_sessions.py
```

This script tests:
- Session creation and management
- Contextual conversation flow
- Memory persistence and retrieval
- Multiple concurrent sessions
- System statistics with memory data

## Implementation Details

### Memory Architecture
- **Session Storage**: In-memory with configurable persistence
- **Message Threading**: Chronological conversation tracking
- **Context Building**: Dynamic context window management
- **Cleanup Strategy**: Time-based and size-based session cleanup

### Performance Considerations
- Memory usage optimized for concurrent sessions
- Efficient context retrieval for fast response times
- Automatic garbage collection for expired sessions
- Scalable architecture for high-volume usage

### Security Features
- Session ID generation with cryptographic randomness
- Session isolation and data privacy
- Automatic session timeout and cleanup
- Protection against session hijacking

## Configuration

Session management can be configured through environment variables:

```bash
# Maximum sessions to keep in memory
MAX_ACTIVE_SESSIONS=100

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES=60

# Maximum messages per session
MAX_MESSAGES_PER_SESSION=50

# Enable session persistence
ENABLE_SESSION_PERSISTENCE=true
```

This completes the Phase 5 implementation with comprehensive session management and memory capabilities integrated into the multilingual RAG system.
