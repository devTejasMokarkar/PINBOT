"""
Refactored FastAPI Web Service for AI Agent

Clean architecture with proper separation of concerns, error handling, and validation.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Import refactored components
from src.config import config
from src.schemas import (
    QueryRequest, QueryResponse, DocumentUploadResponse, 
    HealthResponse, ErrorResponse
)
from src.exceptions import (
    AIServiceException, QuotaExceededException, 
    DocumentProcessingException, InvalidRequestException
)
from src.services.ai_service import AIService
from src.middleware.error_handler import error_handler_middleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format,
    filename=config.logging.file_path
)
logger = logging.getLogger(__name__)

# Global AI service instance
ai_service: AIService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ai_service
    
    # Startup
    logger.info("Starting AI Agent Service...")
    try:
        ai_service = AIService(config)
        logger.info("AI Service initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize AI Service: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down AI Agent Service...")

# Initialize FastAPI with proper configuration
app = FastAPI(
    title="AI Agent Service",
    description="Configurable AI Agent with RAG capabilities",
    version="2.0.0",
    lifespan=lifespan
)

# Add error handling middleware
app.middleware("http")(error_handler_middleware)

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with chat interface."""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with component status."""
    try:
        components = {
            "ai_service": "healthy" if ai_service else "uninitialized",
            "vector_store": "healthy" if ai_service and ai_service.is_healthy() else "unhealthy",
            "quota_manager": "healthy" if ai_service and ai_service.quota_manager else "uninitialized"
        }
        
        overall_status = "healthy" if all(status == "healthy" for status in components.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            version="2.0.0",
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version="2.0.0",
            components={"error": str(e)}
        )

@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Query the AI agent with proper validation and error handling."""
    try:
        if not ai_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Service not initialized"
            )
        
        # Validate request (Pydantic does this automatically)
        response = await ai_service.query(
            question=request.question,
            k=request.k,
            include_sources=request.include_sources
        )
        
        return QueryResponse(**response)
        
    except QuotaExceededException as e:
        logger.warning(f"Quota exceeded: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "QUOTA_EXCEEDED",
                "message": str(e),
                "details": {
                    "model": e.model,
                    "daily_used": e.daily_used,
                    "daily_limit": e.daily_limit,
                    "wait_time": e.wait_time
                }
            }
        )
    except InvalidRequestException as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_REQUEST",
                "message": str(e)
            }
        )
    except DocumentProcessingException as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DOCUMENT_PROCESSING_ERROR",
                "message": "Failed to process documents for query"
            }
        )
    except AIServiceException as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AI_SERVICE_ERROR",
                "message": "Internal AI service error"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )

@app.post("/api/upload", response_model=DocumentUploadResponse)
async def upload_documents():
    """Upload and process documents."""
    try:
        if not ai_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Service not initialized"
            )
        
        result = await ai_service.upload_documents()
        return DocumentUploadResponse(**result)
        
    except DocumentProcessingException as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DOCUMENT_UPLOAD_ERROR",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during upload"
            }
        )

@app.get("/api/stats")
async def get_usage_stats():
    """Get current usage statistics."""
    try:
        if not ai_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Service not initialized"
            )
        
        stats = await ai_service.get_usage_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "STATS_ERROR",
                "message": "Failed to retrieve usage statistics"
            }
        )

if __name__ == "__main__":
    uvicorn.run(
        "app_refactored:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        workers=config.api.workers,
        log_level=config.logging.level.lower()
    )
