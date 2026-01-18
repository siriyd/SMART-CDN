from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "cdn_admin"
    POSTGRES_PASSWORD: str = "cdn_secure_pass_2024"
    POSTGRES_DB: str = "smart_cdn_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # API
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Engine
    # Default to localhost for local development; override with .env or environment variable
    # For Docker: use http://ai-engine:8001
    # For local: use http://localhost:8001
    AI_ENGINE_URL: str = "http://localhost:8001"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Also check parent directory for .env (when running from app/ subdirectory)
        env_file_encoding = 'utf-8'

settings = Settings()

# Log configuration on load (for debugging)
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"AI_ENGINE_URL: {settings.AI_ENGINE_URL}")
    logger.debug(f"POSTGRES_HOST: {settings.POSTGRES_HOST}")
    logger.debug(f"REDIS_HOST: {settings.REDIS_HOST}")
    logger.debug(f"Environment AI_ENGINE_URL: {os.getenv('AI_ENGINE_URL', 'not set')}")


