"""
Document retriever for similarity-based search
"""
from typing import List, Dict, Any, Optional
from src.config.settings import get_settings
from src.utils.logger import setup_logger
from src.knowledge_base.vector_store import VectorStore


class DocumentRetriever:
    """Handles document retrieval based on query similarity"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        self.vector_store = VectorStore()
    
    def retrieve_documents(self, query_data: Dict[str, Any], 
                         k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents based on query
        
        Args:
            query_data: Processed query data from QueryProcessor
            k: Number of documents to retrieve
            
        Returns:
            List of relevant document chunks with metadata
        """
        query_embedding = query_data['embedding']
        query_type = query_data['query_type']
        
        # Determine content type filter based on query
        content_type = self._get_content_type_filter(query_type)
        
        # Search vector store
        search_results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=k,
            content_type=content_type
        )
        
        # Rank and filter results
        ranked_results = self._rank_results(search_results, query_data)
        
        return ranked_results
    
    def _get_content_type_filter(self, query_type: str) -> Optional[str]:
        """
        Determine content type filter based on query type
        
        Args:
            query_type: Type of query (mcq, factual, general)
            
        Returns:
            Content type filter or None for no filter
        """
        if query_type == 'mcq':
            return 'mcq'
        # For factual and general queries, search all content types
        return None
    
    def _rank_results(self, search_results: Dict[str, Any], 
                     query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank and process search results
        
        Args:
            search_results: Raw search results from vector store
            query_data: Processed query data
            
        Returns:
            Ranked list of document chunks
        """
        documents = search_results['documents']
        metadatas = search_results['metadatas']
        distances = search_results['distances']
        ids = search_results['ids']
        
        ranked_results = []
        
        for i, (doc, metadata, distance, doc_id) in enumerate(
            zip(documents, metadatas, distances, ids)
        ):
            # Calculate relevance score (lower distance = higher relevance)
            relevance_score = 1.0 - distance if distance <= 1.0 else 0.0
            
            # Apply query-specific scoring adjustments
            adjusted_score = self._adjust_relevance_score(
                relevance_score, metadata, query_data
            )
            
            result = {
                'text': doc,
                'metadata': metadata,
                'relevance_score': adjusted_score,
                'distance': distance,
                'document_id': doc_id,
                'rank': i + 1
            }
            
            ranked_results.append(result)
        
        # Sort by adjusted relevance score
        ranked_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Filter out low-relevance results
        min_relevance = 0.3
        filtered_results = [
            result for result in ranked_results 
            if result['relevance_score'] >= min_relevance
        ]
        
        return filtered_results
    
    def _adjust_relevance_score(self, base_score: float, 
                               metadata: Dict[str, Any],
                               query_data: Dict[str, Any]) -> float:
        """
        Adjust relevance score based on metadata and query characteristics
        
        Args:
            base_score: Base relevance score from similarity
            metadata: Document metadata
            query_data: Query information
            
        Returns:
            Adjusted relevance score
        """
        adjusted_score = base_score
        
        # Boost MCQ results for MCQ queries
        if (query_data['query_type'] == 'mcq' and 
            metadata.get('content_type') == 'mcq'):
            adjusted_score *= 1.3
        
        # Slight boost for text content for factual queries
        if (query_data['query_type'] == 'factual' and 
            metadata.get('content_type') == 'text'):
            adjusted_score *= 1.1
        
        # Ensure score doesn't exceed 1.0
        return min(adjusted_score, 1.0)
