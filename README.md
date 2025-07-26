# Multilingual RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system capable of processing Bengali HSC textbook content and responding to queries in both Bengali and English languages.

## Project Overview

This system processes the HSC26 Bangla 1st paper PDF document to create a knowledge base that can answer questions accurately using semantic search and generative AI. The system uses Google Gemini for both embeddings and text generation, with support for multilingual query processing.

## Features

- **Multilingual Support**: Handles queries in both Bengali and English
- **Bengali PDF Processing**: Advanced text extraction and processing for Bengali content
- **Semantic Search**: Uses Gemini embeddings for accurate document retrieval
- **Memory Management**: Maintains conversation history and document context
- **Structured Content**: Processes MCQs, glossary, essays, and exam references
- **Clean Architecture**: Modular, maintainable codebase following best practices

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Bengali PDF document (HSC26-Bangla1st-Paper.pdf)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/Multilingual-RAG-System.git
   cd Multilingual-RAG-System
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv

   # On Linux/Mac
   source .venv/bin/activate

   # On Windows
   .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configurations
   ```

5. **Place PDF document**
   ```bash
   # Ensure HSC26-Bangla1st-Paper.pdf is in the data/ directory
   mkdir -p data
   # Copy your PDF file here
   ```

### Configuration

Edit the `.env` file with your settings:

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional (defaults provided)
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
CHROMA_DB_PATH=./data/chroma_db
CHUNK_SIZE=512
LOG_LEVEL=INFO
```

## Project Structure

```
Multilingual-RAG-System/
├── .env.example              # Environment configuration template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── data/                   # PDF documents and data files
│   └── HSC26-Bangla1st-Paper.pdf
├── src/                    # Source code
│   ├── __init__.py
│   ├── config/            # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py    # Settings and environment variables
│   └── utils/             # Utility functions
│       ├── __init__.py
│       └── logger.py      # Logging configuration
├── data/                  # Generated data and vector databases
├── logs/                  # Application logs
└── tests/                 # Test files (coming in later phases)
```

## Development Phases

This project is developed in incremental phases:

- **Phase 1**: COMPLETED - Project setup and environment configuration
- **Phase 2**: IN PROGRESS - Document processing pipeline (next)
- **Phase 3**: Knowledge base construction
- **Phase 4**: RAG core implementation
- **Phase 5**: Memory management system
- **Phase 6**: API development (bonus)
- **Phase 7**: Evaluation system (bonus)

## Usage Examples

### Basic Configuration Test

```python
from src.config.settings import Settings
from src.utils.logger import get_logger

# Initialize settings
settings = Settings()
logger = get_logger("main")

# Validate configuration
try:
    settings.validate_configuration()
    logger.info("Configuration validated successfully")
    print(settings)
except ValueError as e:
    logger.error(f"Configuration error: {e}")
```

### Sample Test Cases

Once the system is complete, it will handle queries like:

**Bengali Queries:**

- অনুপমের ভাষায় সুপুরুষ কাকে বলা হয়েছে?
- কাকে অনুপমের ভাগ্য দেবতা বলে উল্লেখ করা হয়েছে?
- বিয়ের সময় কল্যাণীর প্রকৃত বয়স কত ছিল?

**English Queries:**

- Who is referred to as 'সুপুরুষ' in Anupam's language?
- What was Kalyani's actual age at the time of marriage?

## Technology Stack

- **Language**: Python 3.8+
- **LLM**: Google Gemini (gemini-2.5-flash)
- **Embeddings**: Gemini Embedding (gemini-embedding-001)
- **Vector Database**: ChromaDB
- **PDF Processing**: PyMuPDF, pdfplumber, PyPDF2
- **Web Framework**: FastAPI (bonus feature)
- **Testing**: pytest
- **Logging**: colorlog with structured logging
