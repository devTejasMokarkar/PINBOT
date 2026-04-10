"""
Configuration Management

Centralized configuration with validation and environment-specific settings.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from src.exceptions import ConfigurationException

@dataclass
class DatabaseConfig:
    """Database configuration"""
    vector_db_path: str = "./vector_db"
    docs_path: str = "./documents"
    uploads_path: str = "./Uploads"

@dataclass
class AIConfig:
    """AI model configuration"""
    google_api_key: str
    chat_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"
    temperature: float = 0.1
    max_retries: int = 0
    chunk_size: int = 1000
    chunk_overlap: int = 200

@dataclass
class APIConfig:
    """API configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    workers: int = 1

@dataclass
class QuotaConfig:
    """Quota configuration"""
    daily_limit: int = 20
    minute_limit: int = 15
    enable_tracking: bool = True

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None

class Config:
    """Main configuration class"""
    
    def __init__(self, env_file: Optional[str] = None):
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Initialize configurations
        self.database = self._load_database_config()
        self.ai = self._load_ai_config()
        self.api = self._load_api_config()
        self.quota = self._load_quota_config()
        self.logging = self._load_logging_config()
        
        # Validate configuration
        self._validate()
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            vector_db_path=os.getenv("VECTOR_DB_PATH", "./vector_db"),
            docs_path=os.getenv("DOCS_PATH", "./documents"),
            uploads_path=os.getenv("UPLOADS_PATH", "./Uploads")
        )
    
    def _load_ai_config(self) -> AIConfig:
        """Load AI configuration"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ConfigurationException("GOOGLE_API_KEY is required")
        
        return AIConfig(
            google_api_key=api_key,
            chat_model=os.getenv("CHAT_MODEL", "gemini-2.5-flash"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001"),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.1")),
            max_retries=int(os.getenv("AI_MAX_RETRIES", "0")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200"))
        )
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration"""
        return APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            reload=os.getenv("RELOAD", "false").lower() == "true",
            workers=int(os.getenv("WORKERS", "1"))
        )
    
    def _load_quota_config(self) -> QuotaConfig:
        """Load quota configuration"""
        return QuotaConfig(
            daily_limit=int(os.getenv("DAILY_QUOTA_LIMIT", "20")),
            minute_limit=int(os.getenv("MINUTE_QUOTA_LIMIT", "15")),
            enable_tracking=os.getenv("ENABLE_QUOTA_TRACKING", "true").lower() == "true"
        )
    
    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration"""
        return LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=os.getenv("LOG_FILE_PATH")
        )
    
    def _validate(self):
        """Validate configuration"""
        # Validate paths
        Path(self.database.uploads_path).mkdir(exist_ok=True)
        Path(self.database.vector_db_path).mkdir(exist_ok=True)
        Path(self.database.docs_path).mkdir(exist_ok=True)
        
        # Validate AI config
        if not self.ai.google_api_key:
            raise ConfigurationException("Google API key is required")
        
        if self.ai.temperature < 0 or self.ai.temperature > 2:
            raise ConfigurationException("Temperature must be between 0 and 2")
        
        # Validate API config
        if self.api.port < 1 or self.api.port > 65535:
            raise ConfigurationException("Port must be between 1 and 65535")
        
        # Validate quota config
        if self.quota.daily_limit < 1:
            raise ConfigurationException("Daily quota limit must be positive")
        
        if self.quota.minute_limit < 1:
            raise ConfigurationException("Minute quota limit must be positive")
    
    def get_env_file_path(self) -> str:
        """Get current .env file path"""
        return ".env"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "database": self.database.__dict__,
            "ai": {k: v for k, v in self.ai.__dict__.items() if k != "google_api_key"},
            "api": self.api.__dict__,
            "quota": self.quota.__dict__,
            "logging": self.logging.__dict__
        }

# Global configuration instance
config = Config()
