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
                         retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate response based on query and retrieved documents
        
        Args:
            query_data: Processed query information
            retrieved_docs: List of relevant documents
            
        Returns:
            Generated response with metadata
        """
        if not retrieved_docs:
            return self._generate_no_context_response(query_data)
        
        # Prepare context from retrieved documents
        context = self._prepare_context(retrieved_docs)
        
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
- তথ্য খুঁজে না পেলে স্পষ্টভাবে বলুন"""
        
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
- If the answer is not available, clearly state that the information is not found"""
        
        if query_type == 'mcq':
            base_prompt += "\n- For multiple choice questions, provide the correct answer"
        
        return base_prompt + "\n\nAnswer:"
    
    def _generate_no_context_response(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response when no relevant context is found"""
        language = query_data['language']
        
        if language == 'bn':
            answer = "দুঃখিত, আপনার প্রশ্নের সাথে সম্পর্কিত কোনো তথ্য খুঁজে পাওয়া যায়নি। অন্যভাবে প্রশ্ন করার চেষ্টা করুন।"
        else:
            answer = "Sorry, I couldn't find any relevant information for your question. Please try rephrasing your question."
        
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
