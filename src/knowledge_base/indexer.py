"""
Knowledge base indexer - orchestrates the entire indexing process
"""
import os
from typing import List
from src.config.settings import get_settings
from src.utils.logger import setup_logger
from src.knowledge_base.smart_chunker import SmartContentChunker
from src.knowledge_base.embedding_service import EmbeddingService
from src.knowledge_base.vector_store import VectorStore


class KnowledgeBaseIndexer:
    """Orchestrates the knowledge base construction process"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = setup_logger(__name__)
        
        # Initialize components
        self.chunker = SmartContentChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
    
    def index_documents(self, base_path: str) -> None:
        """
        Index all document files from the processed documents directory
        
        Args:
            base_path: Base path to processed documents directory
        """
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"Base directory not found: {base_path}")
        
        self.logger.info(f"Starting enhanced indexing process for: {base_path}")
        
        # Step 1: Process separated content files with smart chunking
        self.logger.info("Processing separated content with smart chunking...")
        chunks = self.chunker.chunk_separated_content_only(base_path)
        self.logger.info(f"Created {len(chunks)} optimized chunks with content-aware algorithms")
        
        if not chunks:
            self.logger.warning("No chunks created from documents")
            return
        
        # Step 2: Generate embeddings (without rate limiting)
        self.logger.info("Generating embeddings at full speed...")
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_service.generate_embeddings(chunk_texts)
        self.logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Step 3: Store in vector database
        self.logger.info("Storing in vector database...")
        self.vector_store.add_documents(chunks, embeddings)
        
        self.logger.info("Smart content-aware indexing completed successfully")
    
    def rebuild_index(self, base_path: str) -> None:
        """
        Rebuild the entire index from all processed documents
        
        Args:
            base_path: Base path to processed documents directory
        """
        self.logger.info("Rebuilding knowledge base with adaptive chunking...")
        
        # Clear existing data
        self.vector_store.clear_collection()
        
        # Index all documents with adaptive strategies
        self.index_documents(base_path)
        
        self.logger.info("Adaptive index rebuild completed")
    
    def get_index_stats(self) -> dict:
        """Get statistics about the current index"""
        return self.vector_store.get_collection_info()


def main():
    """Main function to index all HSC documents"""
    indexer = KnowledgeBaseIndexer()
    
    # Path to the processed documents directory
    base_path = "/home/tamjid/Codes/Projects/Multilingual_RAG_SYSTEM_10MS/processed_documents"
    
    try:
        indexer.rebuild_index(base_path)
        
        # Print stats
        stats = indexer.get_index_stats()
        print("\nAdaptive Indexing Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error during indexing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
