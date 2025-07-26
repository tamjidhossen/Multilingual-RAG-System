"""
Embedding service using Gemini embedding model with smart rate limiting
"""
import time
import random
from typing import List, Dict, Any
import google.generativeai as genai
from src.config.settings import get_settings
from src.utils.logger import setup_logger


class EmbeddingService:
    """Handles text embedding generation using Gemini with smart rate limiting"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        
        # Configure Gemini
        genai.configure(api_key=self.settings.google_api_key)
        self.model = self.settings.embedding_model
        
        # Very conservative rate limiting for Gemini API Free tier
        # Free tier: 100 RPM = 1.67 RPS, but being ultra-safe due to quota issues
        self.base_delay = 2.0   # 2 seconds = 30 RPM (well under 100 RPM limit)
        self.max_delay = 120.0  # 2 minutes maximum delay
        self.retry_attempts = 3  # Reduced retries to avoid quota waste
        
    def generate_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        """
        Generate embeddings for a list of texts with smart rate limiting
        
        Args:
            texts: List of text strings
            task_type: Type of embedding task (RETRIEVAL_DOCUMENT, QUESTION_ANSWERING, etc.)
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        self.logger.info(f"Starting embedding generation for {len(texts)} texts with rate limiting")
        
        for i, text in enumerate(texts):
            success = False
            
            for attempt in range(self.retry_attempts):
                try:
                    # Conservative rate limiting for Free tier (100 RPM limit)
                    if i > 0:
                        # 2s base + jitter = ~28 RPM (very safe under 100 RPM limit)
                        delay = self.base_delay + random.uniform(0, 0.1)
                        time.sleep(delay)
                    
                    embedding = genai.embed_content(
                        model=f"models/{self.model}",
                        content=text,
                        task_type=task_type
                    )
                    
                    embeddings.append(embedding['embedding'])
                    success = True
                    
                    if (i + 1) % 25 == 0:
                        self.logger.info(f"Generated embeddings for {i + 1}/{len(texts)} texts")
                    
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        # Rate limit or quota error - exponential backoff
                        backoff_delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                        self.logger.warning(f"Rate limit hit at text {i + 1}, attempt {attempt + 1}. Waiting {backoff_delay:.1f}s...")
                        time.sleep(backoff_delay)
                    else:
                        self.logger.error(f"Error generating embedding for text {i + 1}: {e}")
                        break  # Non-rate-limit error, don't retry
            
            if not success:
                self.logger.error(f"Failed to generate embedding for text {i + 1} after {self.retry_attempts} attempts")
                # Add zero vector as fallback
                embeddings.append([0.0] * self.settings.embedding_dimension)
        
        self.logger.info(f"Completed embedding generation: {len([e for e in embeddings if sum(e) != 0])}/{len(texts)} successful")
        return embeddings
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a single query with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                embedding = genai.embed_content(
                    model=f"models/{self.model}",
                    content=query,
                    task_type="QUESTION_ANSWERING"
                )
                return embedding['embedding']
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    backoff_delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                    self.logger.warning(f"Rate limit on query embedding, waiting {backoff_delay:.1f}s...")
                    time.sleep(backoff_delay)
                else:
                    self.logger.error(f"Error generating query embedding: {e}")
                    break
        
        self.logger.error("Failed to generate query embedding after retries")
        return [0.0] * self.settings.embedding_dimension
