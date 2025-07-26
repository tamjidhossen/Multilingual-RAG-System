"""
Multilingual RAG System
A comprehensive RAG system for Bengali and English text processing
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .config.settings import Settings

# Initialize global settings instance
settings = Settings()

__all__ = ["settings"]
