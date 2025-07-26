"""
Settings configuration for the Multilingual RAG System
Handles environment variables and application configuration
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # Project paths
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.PROJECT_ROOT = self.BASE_DIR
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        
        # Create directories if they don't exist
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        
        # Gemini API Configuration
        self.GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        
        # ChromaDB Configuration
        self.CHROMA_DB_PATH: Path = Path(os.getenv("CHROMA_DB_PATH", "./data/chroma_db"))
        self.COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "hsc_bangla_documents")
        
        # Embedding Configuration
        self.EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "768"))
        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
        self.CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
        
        # PDF Processing Configuration
        self.PDF_PATH: Path = Path(os.getenv("PDF_PATH", "./Data/HSC26-Bangla1st-Paper.pdf"))
        self.GEMINI_ENHANCE_THRESHOLD: float = float(
            os.getenv("GEMINI_ENHANCE_THRESHOLD", "0.8")
        )
        self.GEMINI_MAX_DAILY_REQUESTS: int = int(
            os.getenv("GEMINI_MAX_DAILY_REQUESTS", "100")
        )
        
        # API Configuration
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8000"))
        self.API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
        
        # Logging Configuration
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE: Path = self.LOGS_DIR / os.getenv("LOG_FILE", "rag_system.log")
        
        # LangSmith Configuration
        self.LANGCHAIN_TRACING_V2: bool = (
            os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        )
        self.LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
        self.LANGCHAIN_PROJECT: str = os.getenv(
            "LANGCHAIN_PROJECT", "multilingual-rag-system"
        )
        
        # Development Configuration
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    def validate_configuration(self) -> bool:
        """Validate required configuration settings"""
        missing_configs = []
        
        if not self.GOOGLE_API_KEY:
            missing_configs.append("GOOGLE_API_KEY")
        
        if not self.PDF_PATH.exists():
            missing_configs.append(f"PDF_PATH: {self.PDF_PATH}")
        
        if missing_configs:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_configs)}"
            )
        
        return True
    
    def get_chroma_config(self) -> dict:
        """Get ChromaDB configuration"""
        return {
            "path": str(self.CHROMA_DB_PATH),
            "collection_name": self.COLLECTION_NAME,
        }
    
    def get_embedding_config(self) -> dict:
        """Get embedding configuration"""
        return {
            "model": self.EMBEDDING_MODEL,
            "dimension": self.EMBEDDING_DIMENSION,
            "api_key": self.GOOGLE_API_KEY,
        }
    
    def __str__(self) -> str:
        """String representation of settings (excluding sensitive data)"""
        return f"""
        Settings Configuration:
        - Environment: {self.ENVIRONMENT}
        - Debug: {self.DEBUG}
        - Gemini Model: {self.GEMINI_MODEL}
        - Embedding Model: {self.EMBEDDING_MODEL}
        - ChromaDB Path: {self.CHROMA_DB_PATH}
        - Chunk Size: {self.CHUNK_SIZE}
        - Log Level: {self.LOG_LEVEL}
        """
