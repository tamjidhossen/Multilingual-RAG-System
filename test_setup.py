#!/usr/bin/env python3
"""
Setup verification script for Phase 1
Tests basic configuration and environment setup
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_phase1_setup():
    """Test Phase 1 setup and configuration"""
    print("Testing Phase 1 Setup...\n")
    
    # Test 1: Import configuration
    try:
        from src.config.settings import Settings
        print("[PASS] Configuration module imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import Settings: {e}")
        return False
    
    # Test 2: Import logger
    try:
        from src.utils.logger import get_logger, setup_logger
        print("[PASS] Logger module imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import logger: {e}")
        return False
    
    # Test 3: Initialize settings
    try:
        settings = Settings()
        print("[PASS] Settings initialized successfully")
        print(f"   - Environment: {settings.ENVIRONMENT}")
        print(f"   - Debug: {settings.DEBUG}")
        print(f"   - Log Level: {settings.LOG_LEVEL}")
    except Exception as e:
        print(f"[FAIL] Failed to initialize settings: {e}")
        return False
    
    # Test 4: Initialize logger
    try:
        logger = get_logger("test")
        logger.info("Logger test message")
        print("[PASS] Logger initialized and working")
    except Exception as e:
        print(f"[FAIL] Failed to initialize logger: {e}")
        return False
    
    # Test 5: Check directory structure
    required_dirs = [
        Path("src"),
        Path("src/config"),
        Path("src/utils"),
        Path("data"),
        Path("logs"),
    ]
    
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"[PASS] Directory exists: {dir_path}")
        else:
            print(f"[FAIL] Missing directory: {dir_path}")
            return False
    
    # Test 6: Check required files
    required_files = [
        Path(".env.example"),
        Path("requirements.txt"),
        Path("README.md"),
        Path(".gitignore"),
        Path("src/__init__.py"),
        Path("src/config/__init__.py"),
        Path("src/config/settings.py"),
        Path("src/utils/__init__.py"),
        Path("src/utils/logger.py"),
    ]
    
    for file_path in required_files:
        if file_path.exists():
            print(f"[PASS] File exists: {file_path}")
        else:
            print(f"[FAIL] Missing file: {file_path}")
            return False
    
    # Test 7: Configuration validation (without API key)
    print("\nConfiguration status:")
    if settings.GOOGLE_API_KEY:
        print("[PASS] Google API key is configured")
        try:
            settings.validate_configuration()
            print("[PASS] All required configuration is valid")
        except ValueError as e:
            print(f"[WARN] Configuration validation failed: {e}")
    else:
        print("[WARN] Google API key not configured (expected for initial setup)")
    
    print(f"\nProject structure summary:")
    print(f"   - Project root: {settings.PROJECT_ROOT}")
    print(f"   - Data directory: {settings.DATA_DIR}")
    print(f"   - Logs directory: {settings.LOGS_DIR}")
    print(f"   - PDF path: {settings.PDF_PATH}")
    print(f"   - ChromaDB path: {settings.CHROMA_DB_PATH}")
    print(f"   - Collection name: {settings.COLLECTION_NAME}")
    
    print("\nPhase 1 setup completed successfully!")
    print("\nNext steps:")
    print("1. Add your Google API key to .env file")
    print("2. Activate virtual environment: source .venv/bin/activate")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Ready for Phase 2: Document Processing Pipeline")
    
    return True

if __name__ == "__main__":
    success = test_phase1_setup()
    sys.exit(0 if success else 1)
