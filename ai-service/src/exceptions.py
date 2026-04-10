"""
Custom Exceptions for AI Service

Define specific exception types for better error handling and debugging.
"""

class AIServiceException(Exception):
    """Base exception for AI service errors"""
    pass

class QuotaExceededException(AIServiceException):
    """Raised when API quota is exceeded"""
    def __init__(self, model: str, daily_used: int, daily_limit: int, wait_time: int):
        self.model = model
        self.daily_used = daily_used
        self.daily_limit = daily_limit
        self.wait_time = wait_time
        super().__init__(f"Quota exceeded for {model}: {daily_used}/{daily_limit}")

class DocumentProcessingException(AIServiceException):
    """Raised when document processing fails"""
    pass

class VectorStoreException(AIServiceException):
    """Raised when vector store operations fail"""
    pass

class InvalidRequestException(AIServiceException):
    """Raised when request validation fails"""
    pass

class ConfigurationException(AIServiceException):
    """Raised when configuration is invalid"""
    pass
