"""
Query processor for multilingual queries
"""
import re
from typing import Dict, Any
from src.config.settings import get_settings
from src.utils.logger import setup_logger
from src.knowledge_base.embedding_service import EmbeddingService


class QueryProcessor:
    """Handles query preprocessing and language detection"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        self.embedding_service = EmbeddingService()
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process and analyze the input query
        
        Args:
            query: Raw user query
            
        Returns:
            Dictionary containing processed query information
        """
        # Clean the query
        cleaned_query = self._clean_query(query)
        
        # Detect language
        language = self._detect_language(cleaned_query)
        
        # Generate query embedding
        embedding = self.embedding_service.generate_query_embedding(cleaned_query)
        
        # Determine query type
        query_type = self._classify_query_type(cleaned_query, language)
        
        return {
            'original_query': query,
            'cleaned_query': cleaned_query,
            'language': language,
            'query_type': query_type,
            'embedding': embedding
        }
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query"""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove special characters but keep Bengali punctuation
        query = re.sub(r'[^\u0980-\u09FF\w\s\?\।]', ' ', query)
        
        return query
    
    def _detect_language(self, query: str) -> str:
        """
        Detect if the query is in Bengali or English
        
        Args:
            query: Cleaned query text
            
        Returns:
            Language code ('bn' for Bengali, 'en' for English)
        """
        # Count Bengali characters (Unicode range for Bengali)
        bengali_chars = len(re.findall(r'[\u0980-\u09FF]', query))
        total_chars = len(re.findall(r'[^\s]', query))
        
        if total_chars == 0:
            return 'en'
        
        bengali_ratio = bengali_chars / total_chars
        
        # If more than 30% Bengali characters, consider it Bengali
        return 'bn' if bengali_ratio > 0.3 else 'en'
    
    def _classify_query_type(self, query: str, language: str) -> str:
        """
        Classify the type of query (mcq, factual, general)
        
        Args:
            query: Cleaned query
            language: Detected language
            
        Returns:
            Query type string
        """
        query_lower = query.lower()
        
        # Bengali question indicators
        bengali_question_words = ['কী', 'কি', 'কে', 'কোন', 'কার', 'কেন', 'কিভাবে', 'কখন', 'কোথায়']
        
        # English question indicators  
        english_question_words = ['what', 'who', 'when', 'where', 'why', 'how', 'which']
        
        # MCQ related terms
        mcq_terms = ['অপশন', 'সঠিক উত্তর', 'option', 'correct answer', 'choose', 'select']
        
        # Check for MCQ type
        for term in mcq_terms:
            if term.lower() in query_lower:
                return 'mcq'
        
        # Check for factual questions
        question_words = bengali_question_words if language == 'bn' else english_question_words
        for word in question_words:
            if word.lower() in query_lower:
                return 'factual'
        
        return 'general'
