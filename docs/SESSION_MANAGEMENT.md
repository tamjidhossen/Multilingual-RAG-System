# Session Management API Documentation

## Overview
The Multilingual RAG System now includes comprehensive session management capabilities as part of Phase 5 implementation. This allows for persistent conversation history, context retention, and user-specific memory management.

## Session Management Endpoints

### 1. Create New Session
**POST** `/session/create`

Creates a new chat session with unique session ID.

**Response:**
```json
{
    "session_id": "sess_1234567890abcdef",
    "message": "Session created successfully"
}
```

### 2. Get Session Statistics
**GET** `/session/{session_id}/stats`

Retrieves statistics for a specific session.

**Response:**
```json
{
    "session_id": "sess_1234567890abcdef",
    "message_count": 5,
    "avg_response_time": 2.34,
    "languages_used": ["bengali", "english"],
    "created_at": "2024-01-01T10:00:00Z",
    "last_activity": "2024-01-01T10:30:00Z"
}
```

### 3. Get Session History
**GET** `/session/{session_id}/history`

Retrieves complete chat history for a session.

**Response:**
```json
{
    "session_id": "sess_1234567890abcdef",
    "messages": [
        {
            "id": "msg_001",
            "user_query": "বাংলা ব্যাকরণ কি?",
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
