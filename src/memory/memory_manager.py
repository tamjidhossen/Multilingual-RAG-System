"""
Memory Manager for Multilingual RAG System
Handles short-term (chat history) and long-term (document corpus) memory
"""
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from src.config.settings import get_settings
from src.utils.logger import setup_logger


@dataclass
class ChatMessage:
    """Represents a single chat message"""
    timestamp: float
    query: str
    response: str
    language: str
    confidence: float
    session_id: str
    sources_used: List[str]


@dataclass
class ChatSession:
    """Represents a chat session with multiple messages"""
    session_id: str
    created_at: float
    last_activity: float
    messages: List[ChatMessage]
    message_count: int


class MemoryManager:
    """Manages short-term and long-term memory for the RAG system"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        
        # Memory storage paths
        self.memory_dir = self.settings.PROJECT_ROOT / "memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        self.sessions_file = self.memory_dir / "chat_sessions.json"
        self.long_term_stats_file = self.memory_dir / "long_term_stats.json"
        
        # In-memory storage for active sessions
        self.active_sessions: Dict[str, ChatSession] = {}
        
        # Configuration
        self.max_session_memory = 50  # Maximum messages per session
        self.session_timeout = 3600  # 1 hour in seconds
        self.max_active_sessions = 100
        
        # Load existing sessions
        self._load_sessions()
        
        self.logger.info("Memory Manager initialized")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{int(time.time())}_{hash(str(time.time())) % 10000}"
    
    def _load_sessions(self):
        """Load chat sessions from disk"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for session_data in data.get('sessions', []):
                    session = ChatSession(**session_data)
                    # Convert message dicts back to ChatMessage objects
                    session.messages = [ChatMessage(**msg) for msg in session.messages]
                    self.active_sessions[session.session_id] = session
                    
                self.logger.info(f"Loaded {len(self.active_sessions)} chat sessions")
            except Exception as e:
                self.logger.error(f"Error loading sessions: {e}")
    
    def _save_sessions(self):
        """Save chat sessions to disk"""
        try:
            # Convert to serializable format
            sessions_data = []
            for session in self.active_sessions.values():
                session_dict = asdict(session)
                sessions_data.append(session_dict)
            
            data = {
                'sessions': sessions_data,
                'last_updated': time.time()
            }
            
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving sessions: {e}")
    
    def _cleanup_old_sessions(self):
        """Remove old inactive sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def create_session(self) -> str:
        """Create a new chat session"""
        session_id = self._generate_session_id()
        current_time = time.time()
        
        session = ChatSession(
            session_id=session_id,
            created_at=current_time,
            last_activity=current_time,
            messages=[],
            message_count=0
        )
        
        self.active_sessions[session_id] = session
        
        # Cleanup if too many active sessions
        if len(self.active_sessions) > self.max_active_sessions:
            self._cleanup_old_sessions()
        
        self.logger.info(f"Created new session: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, query: str, response: str, 
                   language: str, confidence: float, sources: List[str]) -> bool:
        """Add a message to a chat session"""
        if session_id not in self.active_sessions:
            # Create session if it doesn't exist
            self.active_sessions[session_id] = ChatSession(
                session_id=session_id,
                created_at=time.time(),
                last_activity=time.time(),
                messages=[],
                message_count=0
            )
        
        session = self.active_sessions[session_id]
        current_time = time.time()
        
        message = ChatMessage(
            timestamp=current_time,
            query=query,
            response=response,
            language=language,
            confidence=confidence,
            session_id=session_id,
            sources_used=sources
        )
        
        session.messages.append(message)
        session.message_count += 1
        session.last_activity = current_time
        
        # Limit session memory
        if len(session.messages) > self.max_session_memory:
            session.messages = session.messages[-self.max_session_memory:]
        
        # Periodically save sessions
        if session.message_count % 5 == 0:
            self._save_sessions()
        
        return True
    
    def get_session_history(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Get recent messages from a session"""
        if session_id not in self.active_sessions:
            return []
        
        session = self.active_sessions[session_id]
        return session.messages[-limit:] if session.messages else []
    
    def get_context_for_query(self, session_id: str, current_query: str, 
                             limit: int = 3) -> str:
        """Get contextual information from recent chat history"""
        history = self.get_session_history(session_id, limit)
        
        if not history:
            return ""
        
        # Build context from recent exchanges
        context_parts = []
        for message in history[-limit:]:
            context_parts.append(f"Previous Q: {message.query}")
            context_parts.append(f"Previous A: {message.response}")
        
        context = "\n".join(context_parts)
        return context if len(context) < 500 else context[:500] + "..."
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a specific session"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        languages_used = set()
        total_confidence = 0
        
        for message in session.messages:
            languages_used.add(message.language)
            total_confidence += message.confidence
        
        avg_confidence = total_confidence / len(session.messages) if session.messages else 0
        
        return {
            'session_id': session_id,
            'message_count': session.message_count,
            'languages_used': list(languages_used),
            'avg_confidence': round(avg_confidence, 3),
            'created_at': session.created_at,
            'last_activity': session.last_activity,
            'duration': session.last_activity - session.created_at
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global memory statistics"""
        total_messages = sum(len(session.messages) for session in self.active_sessions.values())
        total_sessions = len(self.active_sessions)
        
        if total_messages == 0:
            return {
                'total_sessions': total_sessions,
                'total_messages': 0,
                'avg_messages_per_session': 0,
                'languages_distribution': {},
                'avg_global_confidence': 0
            }
        
        languages_count = {}
        total_confidence = 0
        
        for session in self.active_sessions.values():
            for message in session.messages:
                lang = message.language
                languages_count[lang] = languages_count.get(lang, 0) + 1
                total_confidence += message.confidence
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'avg_messages_per_session': round(total_messages / total_sessions, 2),
            'languages_distribution': languages_count,
            'avg_global_confidence': round(total_confidence / total_messages, 3)
        }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self._save_sessions()
            self.logger.info(f"Cleared session: {session_id}")
            return True
        return False
    
    def save_and_cleanup(self):
        """Save all sessions and cleanup old ones"""
        self._cleanup_old_sessions()
        self._save_sessions()
        self.logger.info("Memory saved and cleaned up")
    
    def get_fallback_response(self, query: str, language: str) -> Dict[str, Any]:
        """Generate fallback response when no context is found"""
        if language == 'bn':
            fallback_responses = [
                "আমার এই বিষয়ে জ্ঞান নেই। আরো নির্দিষ্ট প্রশ্ন করার চেষ্টা করুন।",
                "এই প্রশ্নের উত্তর আমার জানা নেই। অন্যভাবে জিজ্ঞাসা করুন।",
                "আমি এই বিষয়ে তথ্য খুঁজে পাচ্ছি না। আরো স্পষ্ট প্রশ্ন করুন।"
            ]
            answer = fallback_responses[hash(query) % len(fallback_responses)]
        else:
            fallback_responses = [
                "I don't have knowledge about this. Please try asking more specifically.",
                "I cannot find information about this. Please rephrase your question.",
                "I don't have data on this topic. Try asking in a different way."
            ]
            answer = fallback_responses[hash(query) % len(fallback_responses)]
        
        return {
            'answer': answer,
            'query': query,
            'language': language,
            'context_used': 0,
            'sources': [],
            'confidence': 0.0,
            'fallback': True
        }


def get_memory_manager() -> MemoryManager:
    """Get singleton instance of memory manager"""
    if not hasattr(get_memory_manager, '_instance'):
        get_memory_manager._instance = MemoryManager()
    return get_memory_manager._instance
