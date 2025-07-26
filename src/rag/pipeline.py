"""
RAG Pipeline - orchestrates the complete RAG workflow
"""
from typing import Dict, Any, Optional
from src.config.settings import get_settings
from src.utils.logger import setup_logger
from src.rag.query_processor import QueryProcessor
from src.rag.retriever import DocumentRetriever
from src.rag.generator import ResponseGenerator
from src.memory.memory_manager import get_memory_manager


class RAGPipeline:
    """Main RAG pipeline that orchestrates query processing, retrieval, and generation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        
        # Initialize components
        self.query_processor = QueryProcessor()
        self.retriever = DocumentRetriever()
        self.generator = ResponseGenerator()
        self.memory_manager = get_memory_manager()
        
        self.logger.info("RAG Pipeline initialized successfully")
    
    def process_query(self, query: str, k: int = 5, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a complete RAG query with memory support
        
        Args:
            query: User query in Bengali or English
            k: Number of documents to retrieve
            session_id: Optional session ID for memory management
            
        Returns:
            Complete response with answer and metadata
        """
        try:
            self.logger.info(f"Processing query: {query[:50]}...")
            
            # Create session if not provided
            if session_id is None:
                session_id = self.memory_manager.create_session()
            
            # Get context from chat history
            chat_context = self.memory_manager.get_context_for_query(session_id, query)
            
            # Step 1: Process the query
            query_data = self.query_processor.process_query(query)
            self.logger.info(f"Query language: {query_data['language']}, type: {query_data['query_type']}")
            
            # Step 2: Retrieve relevant documents
            retrieved_docs = self.retriever.retrieve_documents(query_data, k=k)
            self.logger.info(f"Retrieved {len(retrieved_docs)} relevant documents")
            
            # Step 3: Generate response
            if retrieved_docs:
                response = self.generator.generate_response(query_data, retrieved_docs)
            else:
                # Use fallback from memory manager
                response = self.memory_manager.get_fallback_response(
                    query, query_data['language']
                )
            
            # Add pipeline metadata
            response['pipeline_info'] = {
                'query_processed': True,
                'documents_retrieved': len(retrieved_docs),
                'query_language': query_data['language'],
                'query_type': query_data['query_type'],
                'session_id': session_id,
                'chat_context_used': bool(chat_context)
            }
            
            # Save to memory
            self.memory_manager.add_message(
                session_id=session_id,
                query=query,
                response=response['answer'],
                language=query_data['language'],
                confidence=response.get('confidence', 0.0),
                sources=response.get('sources', [])
            )
            
            self.logger.info("Query processed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Error in RAG pipeline: {e}")
            
            # Use fallback response
            fallback_response = self.memory_manager.get_fallback_response(
                query, 'unknown'
            )
            fallback_response['error'] = str(e)
            fallback_response['pipeline_info'] = {
                'query_processed': False,
                'documents_retrieved': 0,
                'error_occurred': True,
                'session_id': session_id or 'unknown'
            }
            
            return fallback_response
    
    def _get_error_response(self, query: str) -> str:
        """Generate error response based on detected language"""
        # Simple language detection for error message
        bengali_chars = len([c for c in query if '\u0980' <= c <= '\u09FF'])
        total_chars = len([c for c in query if not c.isspace()])
        
        if total_chars > 0 and bengali_chars / total_chars > 0.3:
            return "দুঃখিত, আপনার প্রশ্ন প্রক্রিয়া করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।"
        else:
            return "Sorry, there was an error processing your question. Please try again."


def main():
    """Test the RAG pipeline with sample queries"""
    pipeline = RAGPipeline()
    
    # Test queries
    test_queries = [
        "অনুপমের বাবা কী করে জীবিকা নির্বাহ করতেন?",
        "কাকে অনুপমের ভাগ্য দেবতা বলে উল্লেখ করা হয়েছে?",
        "Who is referred to as 'সুপুরুষ' in Anupam's language?",
        "What was Kalyani's actual age at the time of marriage?"
    ]
    
    print("Testing RAG Pipeline...")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 30)
        
        try:
            response = pipeline.process_query(query)
            
            print(f"Language: {response['language']}")
            print(f"Answer: {response['answer']}")
            print(f"Confidence: {response['confidence']:.2f}")
            print(f"Sources: {len(response['sources'])}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print()


if __name__ == "__main__":
    main()
