"""
Response generator using Gemini model
"""
from typing import List, Dict, Any
import google.generativeai as genai
from src.config.settings import get_settings
from src.utils.logger import setup_logger


class ResponseGenerator:
    """Generates responses using retrieved context and Gemini model"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        
        # Configure Gemini
        genai.configure(api_key=self.settings.google_api_key)
        self.model = genai.GenerativeModel(self.settings.gemini_model)
    
    def generate_response(self, query_data: Dict[str, Any], 
                         retrieved_docs: List[Dict[str, Any]], 
                         chat_history: List = None) -> Dict[str, Any]:
        """
        Generate response based on query and retrieved documents
        
        Args:
            query_data: Processed query information
            retrieved_docs: List of relevant documents
            chat_history: Previous chat messages for context
            
        Returns:
            Generated response with metadata
        """
        # Check if this is a memory/history related query
        if self._is_memory_query(query_data):
            return self._handle_memory_query(query_data, chat_history)
        
        if not retrieved_docs:
            return self._generate_no_context_response(query_data)
        
        # Prepare context from retrieved documents
        context = self._prepare_context(retrieved_docs)
        
        # Add chat history context if available
        if chat_history:
            context = self._add_chat_context(context, chat_history, query_data['language'])
        
        # Generate prompt based on query language and type
        prompt = self._build_prompt(query_data, context)
        
        try:
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            
            return {
                'answer': response.text,
                'query': query_data['original_query'],
                'language': query_data['language'],
                'context_used': len(retrieved_docs),
                'sources': [doc['document_id'] for doc in retrieved_docs[:3]],
                'confidence': self._calculate_confidence(retrieved_docs)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return {
                'answer': self._get_error_message(query_data['language']),
                'query': query_data['original_query'],
                'language': query_data['language'],
                'context_used': 0,
                'sources': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _prepare_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Prepare context string from retrieved documents"""
        context_parts = []
        
        for doc in retrieved_docs[:5]:
            text = doc['text'].strip()
            if text:
                context_parts.append(text)
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, query_data: Dict[str, Any], context: str) -> str:
        """Build appropriate prompt based on query language and type"""
        query = query_data['cleaned_query']
        language = query_data['language']
        query_type = query_data['query_type']
        
        if language == 'bn':
            return self._build_bengali_prompt(query, context, query_type)
        else:
            return self._build_english_prompt(query, context, query_type)
    
    def _build_bengali_prompt(self, query: str, context: str, query_type: str) -> str:
        """Build Bengali language prompt"""
        base_prompt = f"""আপনি একজন বাংলা সাহিত্যের বিশেষজ্ঞ। নিম্নলিখিত তথ্যের ভিত্তিতে প্রশ্নের উত্তর দিন।

তথ্য:
{context}

প্রশ্ন: {query}

নির্দেশনা:
- শুধুমাত্র প্রদত্ত তথ্যের ভিত্তিতে উত্তর দিন
- উত্তর সংক্ষিপ্ত এবং সঠিক হতে হবে
- তথ্য না জানলে বলুন "আমার এই বিষয়ে জ্ঞান নেই"
- কোনো তথ্যসূত্র বা রেফারেন্স উল্লেখ করবেন না"""
        
        if query_type == 'mcq':
            base_prompt += "\n- বহুনির্বাচনী প্রশ্নের ক্ষেত্রে সঠিক উত্তর দিন"
        
        return base_prompt + "\n\nউত্তর:"
    
    def _build_english_prompt(self, query: str, context: str, query_type: str) -> str:
        """Build English language prompt"""
        base_prompt = f"""You are a helpful assistant specializing in Bengali literature. Answer the question based on the provided information.

Information:
{context}

Question: {query}

Instructions:
- Answer based only on the information provided
- Keep the answer concise and accurate
- If you don't know something, say "I don't have knowledge about this"
- Do not include any source references or citations"""
        
        if query_type == 'mcq':
            base_prompt += "\n- For multiple choice questions, provide the correct answer"
        
        return base_prompt + "\n\nAnswer:"
    
    def _generate_no_context_response(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response when no relevant context is found"""
        language = query_data['language']
        
        if language == 'bn':
            answer = "আমার এই বিষয়ে জ্ঞান নেই। অন্যভাবে প্রশ্ন করার চেষ্টা করুন।"
        else:
            answer = "I don't have knowledge about this. Please try rephrasing your question."
        
        return {
            'answer': answer,
            'query': query_data['original_query'],
            'language': language,
            'context_used': 0,
            'sources': [],
            'confidence': 0.0
        }
    
    def _calculate_confidence(self, retrieved_docs: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on retrieved documents"""
        if not retrieved_docs:
            return 0.0
        
        # Average relevance score of top 3 documents
        top_docs = retrieved_docs[:3]
        avg_relevance = sum(doc['relevance_score'] for doc in top_docs) / len(top_docs)
        
        return min(avg_relevance * 1.2, 1.0)  # Slight boost, cap at 1.0
    
    def _get_error_message(self, language: str) -> str:
        """Get error message in appropriate language"""
        if language == 'bn':
            return "দুঃখিত, উত্তর তৈরি করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।"
        else:
            return "Sorry, there was an error generating the response. Please try again."
    
    def _is_memory_query(self, query_data: Dict[str, Any]) -> bool:
        """Check if the query is asking about conversation history"""
        query = query_data['cleaned_query'].lower()
        language = query_data['language']
        
        if language == 'bn':
            memory_keywords = [
                'আগের প্রশ্ন', 'শেষ প্রশ্ন', 'পূর্বের প্রশ্ন', 'আগে কী জিজ্ঞেস',
                'আগে কি জিজ্ঞেস', 'আগের উত্তর', 'শেষ উত্তর', 'পূর্বের উত্তর',
                'আমার আগের', 'আমার শেষ', 'আমার পূর্বের'
            ]
        else:
            memory_keywords = [
                'my last query', 'my previous query', 'last question', 'previous question',
                'what did i ask', 'what was my question', 'my last question',
                'previous answer', 'last answer', 'what did you say', 'before'
            ]
        
        return any(keyword in query for keyword in memory_keywords)
    
    def _handle_memory_query(self, query_data: Dict[str, Any], chat_history: List) -> Dict[str, Any]:
        """Handle queries about conversation history"""
        language = query_data['language']
        
        if not chat_history or len(chat_history) == 0:
            if language == 'bn':
                answer = "এই কথোপকথনে এখনো কোনো আগের প্রশ্ন নেই।"
            else:
                answer = "There are no previous questions in this conversation yet."
        else:
            # Get the last message from history
            last_message = chat_history[-1]
            
            if language == 'bn':
                if 'প্রশ্ন' in query_data['cleaned_query'] or 'জিজ্ঞেস' in query_data['cleaned_query']:
                    answer = f"আপনার শেষ প্রশ্ন ছিল: \"{last_message.query}\""
                elif 'উত্তর' in query_data['cleaned_query']:
                    answer = f"আমার শেষ উত্তর ছিল: \"{last_message.response}\""
                else:
                    answer = f"আপনার শেষ প্রশ্ন: \"{last_message.query}\"\nআমার উত্তর: \"{last_message.response}\""
            else:
                if 'question' in query_data['cleaned_query'] or 'query' in query_data['cleaned_query'] or 'ask' in query_data['cleaned_query']:
                    answer = f"Your last question was: \"{last_message.query}\""
                elif 'answer' in query_data['cleaned_query'] or 'response' in query_data['cleaned_query'] or 'say' in query_data['cleaned_query']:
                    answer = f"My last answer was: \"{last_message.response}\""
                else:
                    answer = f"Your last question: \"{last_message.query}\"\nMy answer: \"{last_message.response}\""
        
        return {
            'answer': answer,
            'query': query_data['original_query'],
            'language': language,
            'context_used': 0,
            'sources': [],
            'confidence': 1.0,
            'memory_query': True
        }
    
    def _add_chat_context(self, context: str, chat_history: List, language: str) -> str:
        """Add chat history context to the document context"""
        if not chat_history or len(chat_history) == 0:
            return context
        
        # Get last 2 messages for context
        recent_history = chat_history[-2:] if len(chat_history) >= 2 else chat_history
        
        if language == 'bn':
            chat_context = "আগের কথোপকথন:\n"
        else:
            chat_context = "Previous conversation:\n"
        
        for msg in recent_history:
            if language == 'bn':
                chat_context += f"প্রশ্ন: {msg.query}\nউত্তর: {msg.response}\n\n"
            else:
                chat_context += f"Q: {msg.query}\nA: {msg.response}\n\n"
        
        return chat_context + "প্রাসঙ্গিক তথ্য:\n" + context if language == 'bn' else chat_context + "Relevant information:\n" + context
