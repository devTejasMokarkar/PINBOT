"""
Pydantic Schemas for Request/Response Validation

Define data models with validation for API requests and responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re

class QueryRequest(BaseModel):
    """Request model for chat queries"""
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    k: Optional[int] = Field(default=4, ge=1, le=10, description="Number of documents to retrieve")
    include_sources: Optional[bool] = Field(default=True, description="Include source documents")
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty")
        # Basic SQL injection prevention
        if any(keyword in v.lower() for keyword in ['drop table', 'delete from', 'insert into']):
            raise ValueError("Invalid characters in question")
        return v.strip()

class QueryResponse(BaseModel):
    """Response model for chat queries"""
    answer: str = Field(..., description="AI generated answer")
    question: str = Field(..., description="Original question")
    sources: Optional[List[Dict[str, Any]]] = Field(default=[], description="Source documents")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")

class DocumentUploadResponse(BaseModel):
    """Response model for document uploads"""
    status: str = Field(..., description="Upload status")
    documents_processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    error: Optional[str] = Field(default=None, description="Error message if failed")

class UsageStats(BaseModel):
    """Model for usage statistics"""
    daily: Dict[str, Dict[str, int]] = Field(..., description="Daily usage stats")
    minute: Dict[str, Dict[str, int]] = Field(..., description="Minute usage stats")
    limits: Dict[str, Dict[str, int]] = Field(..., description="Usage limits")

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    components: Dict[str, str] = Field(..., description="Component statuses")
