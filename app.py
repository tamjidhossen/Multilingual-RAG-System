#!/usr/bin/env python3
"""
REST API for Multilingual RAG System
"""
import os
import sys
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from src.config.settings import get_settings
from src.rag.pipeline import RAGPipeline
from src.utils.logger import setup_logger

settings = get_settings()
pipeline = None
logger = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global pipeline, logger
    logger = setup_logger(__name__)
    
    logger.info("Starting Multilingual RAG API...")
    try:
        pipeline = RAGPipeline()
        logger.info("RAG Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG Pipeline: {e}")
        raise
    
    yield
    
    logger.info("Shutting down Multilingual RAG API...")

app = FastAPI(
    title="Multilingual RAG System API",
    description="A lightweight REST API for multilingual RAG queries supporting Bengali and English",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    """Request model for RAG queries"""
    query: str = Field(..., min_length=1, max_length=1000, description="User query in Bengali or English")
    k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")

class QueryResponse(BaseModel):
    """Response model for RAG queries"""
    query: str
    answer: str
    language: str
    confidence: float
    context_used: int
    sources: List[str]
    response_time: float
    pipeline_info: Dict[str, Any]
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    timestamp: str
    version: str

class SystemStats(BaseModel):
    """System statistics response"""
    total_queries: int
    avg_response_time: float
    pipeline_ready: bool
    last_query_time: Optional[str]

stats = {
    "total_queries": 0,
    "total_response_time": 0.0,
    "last_query_time": None
}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chat interface"""
    try:
        static_path = settings.PROJECT_ROOT / "static" / "index.html"
        with open(static_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
            <head><title>Multilingual RAG System</title></head>
            <body>
                <h1>Multilingual RAG System API</h1>
                <p>Welcome to the Multilingual RAG System!</p>
                <p><a href="/docs">API Documentation</a></p>
                <p>Chat interface is being prepared...</p>
            </body>
        </html>
        """)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    global pipeline
    
    status = "healthy" if pipeline is not None else "unhealthy"
    message = "RAG Pipeline is ready" if pipeline is not None else "RAG Pipeline not initialized"
    
    return HealthResponse(
        status=status,
        message=message,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        version="1.0.0"
    )

@app.get("/stats", response_model=SystemStats)
async def get_stats():
    """Get system statistics"""
    global stats, pipeline
    
    avg_time = (stats["total_response_time"] / stats["total_queries"]) if stats["total_queries"] > 0 else 0.0
    
    return SystemStats(
        total_queries=stats["total_queries"],
        avg_response_time=round(avg_time, 3),
        pipeline_ready=pipeline is not None,
        last_query_time=stats["last_query_time"]
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a RAG query"""
    global pipeline, stats, logger
    
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG Pipeline is not ready")
    
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: {request.query[:50]}...")
        
        response = pipeline.process_query(request.query, k=request.k)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        stats["total_queries"] += 1
        stats["total_response_time"] += response_time
        stats["last_query_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"Query processed successfully in {response_time:.2f}s")
        
        return QueryResponse(
            query=response.get("query", request.query),
            answer=response.get("answer", ""),
            language=response.get("language", "unknown"),
            confidence=response.get("confidence", 0.0),
            context_used=response.get("context_used", 0),
            sources=response.get("sources", []),
            response_time=round(response_time, 3),
            pipeline_info=response.get("pipeline_info", {}),
            error=response.get("error")
        )
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        
        logger.error(f"Error processing query: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "response_time": round(response_time, 3)
            }
        )

@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    """Chat-friendly endpoint that returns simplified responses"""
    global pipeline, logger
    
    if pipeline is None:
        return JSONResponse(
            status_code=503,
            content={"error": "System is not ready. Please try again later."}
        )
    
    try:
        start_time = time.time()
        response = pipeline.process_query(request.query, k=request.k)
        end_time = time.time()
        
        return {
            "answer": response.get("answer", "Sorry, I couldn't process your question."),
            "language": response.get("language", "unknown"),
            "confidence": response.get("confidence", 0.0),
            "response_time": round(end_time - start_time, 2),
            "sources_count": len(response.get("sources", []))
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Sorry, there was an error processing your message."}
        )

@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "message": "Please check your request format",
            "details": str(exc)
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong. Please try again later."
        }
    )

try:
    static_dir = settings.PROJECT_ROOT / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
except Exception:
    pass

def main():
    """Run the API server"""
    print("MULTILINGUAL RAG SYSTEM API")
    print("=" * 50)
    print("Starting server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Chat Interface: http://localhost:8000/")
    print("Health Check: http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
