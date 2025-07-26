#!/usr/bin/env python3
"""
Quick start script for the Multilingual RAG API
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the RAG API server"""
    print("MULTILINGUAL RAG SYSTEM - API SERVER")
    print("=" * 50)
    print("Starting the API server...")
    print()
    print("Once started, you can access:")
    print("   • Chat Interface: http://localhost:8000/")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • Health Check: http://localhost:8000/health")
    print("   • System Stats: http://localhost:8000/stats")
    print()
    print("To test the API programmatically:")
    print('   curl -X POST "http://localhost:8000/query" \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"query": "অনুপমের ভাষায় সুপুরুষ কাকে বলা হয়েছে?"}\'')
    print()
    print("=" * 50)
    print("Starting server... (Press Ctrl+C to stop)")
    print("=" * 50)
    
    project_root = Path(__file__).parent.absolute()
    
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], cwd=project_root, env=env)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Make sure you have run 'python build_index.py' first")

if __name__ == "__main__":
    main()
