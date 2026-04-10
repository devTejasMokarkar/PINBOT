"""
AI Service Layer

Business logic layer that separates concerns from API controllers.
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

from src.config import Config
from src.rag_pipeline import RAGPipeline
from src.agent_with_persona import AgentWithPersona
from src.exceptions import (
    AIServiceException, QuotaExceededException, 
    DocumentProcessingException, InvalidRequestException
)
from src.schemas import QueryResponse, DocumentUploadResponse

logger = logging.getLogger(__name__)

class AIService:
    """Main AI service handling business logic"""
    
    def __init__(self, config: Config):
        """Initialize AI service with configuration"""
        self.config = config
        self.rag_pipeline = None
        self.agent = None
        self.quota_manager = None
        
        try:
            self._initialize_components()
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise AIServiceException(f"Service initialization failed: {e}")
    
    def _initialize_components(self):
        """Initialize all AI components"""
        try:
            # Initialize RAG pipeline
            self.rag_pipeline = RAGPipeline(
                google_api_key=self.config.ai.google_api_key,
                vector_db_path=self.config.database.vector_db_path,
                docs_path=self.config.database.docs_path
            )
            
            # Initialize agent with persona
            self.agent = AgentWithPersona(
                google_api_key=self.config.ai.google_api_key
            )
            
            # Set default persona
            self.agent.set_persona("General Assistant")
            
            # Get quota manager reference
            self.quota_manager = self.rag_pipeline.free_tier_manager
            
            logger.info("AI service components initialized successfully")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise AIServiceException(f"Failed to initialize components: {e}")
    
    async def query(self, question: str, k: int = 4, include_sources: bool = True) -> Dict[str, Any]:
        """
        Query the AI agent with validation and error handling
        
        Args:
            question: User question
            k: Number of documents to retrieve
            include_sources: Whether to include source documents
            
        Returns:
            Query response dictionary
            
        Raises:
            InvalidRequestException: If question is invalid
            QuotaExceededException: If quota is exceeded
            AIServiceException: For other AI service errors
        """
        try:
            # Validate input
            if not question or not question.strip():
                raise InvalidRequestException("Question cannot be empty")
            
            if len(question) > 1000:
                raise InvalidRequestException("Question too long (max 1000 characters)")
            
            # Check quota before processing
            model = self.config.ai.chat_model
            can_make_request, reason = self.quota_manager.can_make_request(model)
            
            if not can_make_request:
                usage_stats = self.quota_manager.get_usage_stats()
                daily_usage = usage_stats.get('daily', {}).get(model, {})
                raise QuotaExceededException(
                    model=model,
                    daily_used=daily_usage.get('used', 0),
                    daily_limit=daily_usage.get('limit', self.config.quota.daily_limit),
                    wait_time=self.quota_manager.get_wait_time(model)
                )
            
            # Process query through agent
            logger.info(f"Processing query: {question[:100]}...")
            response = self.agent.query_with_persona(
                question=question,
                k=k,
                include_sources=include_sources
            )
            
            # Validate response
            if not response or 'answer' not in response:
                raise AIServiceException("Invalid response from AI agent")
            
            logger.info(f"Query processed successfully")
            return response
            
        except QuotaExceededException:
            # Re-raise quota exceptions
            raise
        except InvalidRequestException:
            # Re-raise validation exceptions
            raise
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise AIServiceException(f"Query processing failed: {e}")
    
    async def upload_documents(self) -> Dict[str, Any]:
        """
        Upload and process documents
        
        Returns:
            Document upload response
            
        Raises:
            DocumentProcessingException: If document processing fails
        """
        try:
            logger.info("Starting document upload process")
            
            # Ingest documents from uploads folder
            result = self.agent.ingest_from_uploads()
            
            if result.get('status') != 'success':
                error_msg = result.get('error', 'Unknown error')
                raise DocumentProcessingException(f"Document ingestion failed: {error_msg}")
            
            logger.info(f"Document upload completed: {result}")
            return result
            
        except DocumentProcessingException:
            raise
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            raise DocumentProcessingException(f"Document upload failed: {e}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics
        
        Returns:
            Usage statistics dictionary
        """
        try:
            if not self.quota_manager:
                return {"error": "Quota manager not initialized"}
            
            stats = self.quota_manager.get_usage_stats()
            logger.info("Usage stats retrieved successfully")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            raise AIServiceException(f"Failed to retrieve usage statistics: {e}")
    
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Check if all components are initialized
            if not self.rag_pipeline or not self.agent or not self.quota_manager:
                return False
            
            # Check vector store
            if not self.rag_pipeline.vector_store:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get service information
        
        Returns:
            Service information dictionary
        """
        return {
            "version": "2.0.0",
            "model": self.config.ai.chat_model,
            "embedding_model": self.config.ai.embedding_model,
            "components": {
                "rag_pipeline": self.rag_pipeline is not None,
                "agent": self.agent is not None,
                "quota_manager": self.quota_manager is not None
            }
        }
