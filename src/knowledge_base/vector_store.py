"""
Vector database implementation using ChromaDB
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from src.config.settings import get_settings
from src.utils.logger import setup_logger


class VectorStore:
    """Manages vector storage and retrieval using ChromaDB"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        
        # Create ChromaDB directory if it doesn't exist
        os.makedirs(self.settings.chroma_db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.settings.chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.settings.collection_name,
            metadata={"description": "HSC Bangla document embeddings"}
        )
        
        self.logger.info(f"Vector store initialized with collection: {self.settings.collection_name}")
    
    def add_documents(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]] = None) -> None:
        """
        Add document texts and their embeddings to the vector store
        
        Args:
            texts: List of text strings
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dictionaries
        """
        if len(texts) != len(embeddings):
            raise ValueError("Number of texts must match number of embeddings")
        
        # Prepare data for ChromaDB
        ids = [f"doc_{i}" for i in range(len(texts))]
        if metadatas is None:
            metadatas = [{"source": "processed_documents"} for _ in texts]
        
        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            self.logger.info(f"Added {len(texts)} documents to vector store")
            
        except Exception as e:
            self.logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def search(self, query_embedding: List[float], n_results: int = 5, 
               content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for similar documents using embedding similarity
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            content_type: Filter by content type (mcq, text, etc.)
            
        Returns:
            Dictionary containing search results
        """
        try:
            # Prepare query filters
            where_clause = {}
            if content_type:
                where_clause["content_type"] = content_type
            
            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            return {
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0],
                'ids': results['ids'][0]
            }
            
        except Exception as e:
            self.logger.error(f"Error searching vector store: {e}")
            return {
                'documents': [],
                'metadatas': [],
                'distances': [],
                'ids': []
            }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            count = self.collection.count()
            return {
                'collection_name': self.settings.collection_name,
                'document_count': count,
                'embedding_dimension': self.settings.embedding_dimension
            }
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")
            return {}
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection"""
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.settings.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.settings.collection_name,
                metadata={"description": "HSC Bangla document embeddings"}
            )
            self.logger.info("Collection cleared successfully")
        except Exception as e:
            self.logger.error(f"Error clearing collection: {e}")
            raise
