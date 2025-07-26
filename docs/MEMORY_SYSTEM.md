# Session Management & Memory System

## Overview

The Multilingual RAG System includes a sophisticated memory management system that maintains conversation history, enables meta-queries about previous interactions, and provides context-aware responses.

## 🧠 Memory Architecture

### Core Components

1. **MemoryManager** (`src/memory/memory_manager.py`)
   - Central memory coordination
   - Session lifecycle management
   - Persistent storage handling

2. **ChatSession** (Data Class)
   - Individual conversation container
   - Message history tracking
   - Session metadata management

3. **ChatMessage** (Data Class)  
   - Individual message representation
   - Timestamp and metadata tracking
   - Language and confidence tracking

## 📊 Session Management

### Session Lifecycle

```python
# 1. Session Creation
session_id = memory_manager.create_session()
# Format: "session_{timestamp}_{random_hash}"

# 2. Message Addition
memory_manager.add_message(
    session_id=session_id,
    query="user query",
    response="system response", 
    language="bn",
    confidence=0.85,
    sources=["doc1", "doc2"]
)

# 3. Session Retrieval
history = memory_manager.get_session_history(session_id, limit=10)

# 4. Session Cleanup (automatic)
# Sessions expire after 1 hour of inactivity
```

### Session Configuration

```python
class MemoryManager:
    def __init__(self):
        self.max_session_memory = 50      # Max messages per session
        self.session_timeout = 3600       # 1 hour timeout
        self.max_active_sessions = 100    # Max concurrent sessions
```

## 🔍 Memory Query Detection

### Supported Memory Queries

#### Bengali Patterns
```python
bengali_memory_keywords = [
    'আগের প্রশ্ন',           # Previous question
    'শেষ প্রশ্ন',             # Last question  
    'পূর্বের প্রশ্ন',          # Earlier question
    'আগে কী জিজ্ঞেস',        # What did I ask before
    'আগে কি জিজ্ঞেস',        # What did I ask before (alternate)
    'আগের উত্তর',            # Previous answer
    'শেষ উত্তর',             # Last answer
    'পূর্বের উত্তর',          # Earlier answer
    'আমার আগের',            # My previous
    'আমার শেষ',             # My last
    'আমার পূর্বের'           # My earlier
]
```

#### English Patterns
```python
english_memory_keywords = [
    'my last query',          # Direct reference
    'my previous query',      # Previous reference
    'last question',          # Last question
    'previous question',      # Previous question
    'what did i ask',         # Past query inquiry
    'what was my question',   # Question recall
    'my last question',       # Direct last question
    'previous answer',        # Previous response
    'last answer',           # Last response
    'what did you say',      # Response recall
    'before'                 # General previous reference
]
```

### Detection Algorithm

```python
def _is_memory_query(self, query_data: Dict[str, Any]) -> bool:
    """Check if query is asking about conversation history"""
    query = query_data['cleaned_query'].lower()
    language = query_data['language']
    
    keywords = bengali_keywords if language == 'bn' else english_keywords
    return any(keyword in query for keyword in keywords)
```

## 💬 Memory Response Generation

### Response Types

#### 1. Question Recall
```python
# Bengali
"আপনার শেষ প্রশ্ন ছিল: \"{last_message.query}\""

# English  
"Your last question was: \"{last_message.query}\""
```

#### 2. Answer Recall
```python
# Bengali
"আমার শেষ উত্তর ছিল: \"{last_message.response}\""

# English
"My last answer was: \"{last_message.response}\""
```

#### 3. Combined Context
```python
# Bengali
"আপনার শেষ প্রশ্ন: \"{query}\"\nআমার উত্তর: \"{response}\""

# English
"Your last question: \"{query}\"\nMy answer: \"{response}\""
```

### Empty History Handling

```python
# Bengali
"এই কথোপকথনে এখনো কোনো আগের প্রশ্ন নেই।"

# English
"There are no previous questions in this conversation yet."
```

## 🗄️ Persistent Storage

### Storage Format (chat_sessions.json)

```json
{
  "sessions": [
    {
      "session_id": "session_1753550133_696",
      "created_at": 1753550133.2646508,
      "last_activity": 1753550145.8374922,
      "messages": [
        {
          "timestamp": 1753550140.1234567,
          "query": "অনুপমের বাবা কী করতেন?",
          "response": "অনুপমের বাবা ওকালতি করতেন।",
          "language": "bn",
          "confidence": 0.85,
          "session_id": "session_1753550133_696",
          "sources_used": ["doc_1", "doc_2"]
        }
      ],
      "message_count": 1
    }
  ],
  "last_updated": 1753550145.8374922
}
```

### Storage Management

- **Auto-Save**: Every 5 messages
- **Session Cleanup**: Removes expired sessions
- **Backup Strategy**: File-based persistence with error recovery
- **Memory Limits**: Configurable message limits per session

## 📈 Statistics & Analytics

### Session Statistics

```python
session_stats = memory_manager.get_session_stats(session_id)
# Returns:
{
    'session_id': 'session_123',
    'message_count': 15,
    'languages_used': ['bn', 'en'],
    'avg_confidence': 0.87,
    'created_at': 1753550133.264,
    'last_activity': 1753550200.123,
    'duration': 66.859  # seconds
}
```

### Global Statistics

```python
global_stats = memory_manager.get_global_stats()
# Returns:
{
    'total_sessions': 25,
    'total_messages': 150,
    'avg_messages_per_session': 6.0,
    'languages_distribution': {'bn': 95, 'en': 55},
    'avg_global_confidence': 0.82
}
```

## 🔧 Integration Points

### RAG Pipeline Integration

```python
class RAGPipeline:
    def process_query(self, query: str, session_id: str = None):
        # 1. Get chat history
        chat_history = self.memory_manager.get_session_history(session_id, limit=5)
        
        # 2. Process query with memory context
        response = self.generator.generate_response(
            query_data, 
            retrieved_docs, 
            chat_history  # Memory context
        )
        
        # 3. Save to memory
        self.memory_manager.add_message(
            session_id=session_id,
            query=query,
            response=response['answer'],
            language=response['language'],
            confidence=response['confidence'],
            sources=response['sources']
        )
```

### API Integration

```python
@app.post("/query")
async def process_query(request: QueryRequest):
    # Memory-aware query processing
    response = pipeline.process_query(
        query=request.query,
        k=request.k,
        session_id=request.session_id  # Session support
    )
    
    return response

@app.post("/session/create")
async def create_session():
    session_id = memory_manager.create_session()
    return {"session_id": session_id, "created": True}
```

## 🧪 Testing Memory System

### Test Coverage

1. **Memory Query Detection**
   ```python
   def test_memory_query_detection():
       # Test Bengali patterns
       assert is_memory_query("আমার শেষ প্রশ্ন কী ছিল?")
       
       # Test English patterns  
       assert is_memory_query("what was my last query?")
   ```

2. **Session Persistence**
   ```python
   def test_session_persistence():
       # Create session and add messages
       session_id = memory_manager.create_session()
       memory_manager.add_message(...)
       
       # Restart system and verify persistence
       new_manager = MemoryManager()
       history = new_manager.get_session_history(session_id)
       assert len(history) > 0
   ```

3. **Memory Response Generation**
   ```python
   def test_memory_responses():
       # Test different memory query types
       response = handle_memory_query("আমার শেষ প্রশ্ন কী?", history)
       assert "আপনার শেষ প্রশ্ন ছিল" in response['answer']
   ```

## 🚀 Performance Considerations

### Memory Usage
- **In-Memory Sessions**: Active sessions kept in memory
- **Lazy Loading**: Sessions loaded on demand
- **Memory Limits**: Configurable per-session message limits

### Storage Optimization
- **Incremental Saves**: Save every N messages
- **Compression**: Consider JSON compression for large histories
- **Cleanup**: Automatic removal of expired sessions

### Scalability
- **Current**: File-based storage suitable for single-instance deployment
- **Future**: Redis/Database backend for multi-instance scaling

## 🔒 Security Considerations

### Data Privacy
- **Session Isolation**: Sessions are completely isolated
- **No Cross-Session Data**: Memory queries cannot access other sessions
- **Configurable Retention**: Sessions auto-expire

### Error Handling
- **Graceful Degradation**: System works without memory if storage fails
- **Recovery**: Automatic recovery from corrupted session files
- **Validation**: Input validation for all memory operations

---

This memory system provides a robust foundation for conversational AI with persistent context awareness and multilingual support.
