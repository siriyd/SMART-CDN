"""
Edge Simulator Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Edge Simulator
    EDGE_SIM_HOST: str = "0.0.0.0"
    EDGE_SIM_PORT: int = 8002
    
    # Origin Server (Backend)
    ORIGIN_SERVER_URL: str = "http://backend:8000"
    
    # Redis Cache
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Edge Configuration
    EDGE_REGIONS: str = "us-east,us-west,eu-west"  # Comma-separated
    EDGE_CACHE_CAPACITY_MB: int = 100
    
    # Cache Settings
    DEFAULT_TTL_SECONDS: int = 3600  # 1 hour default TTL
    CACHE_HIT_LATENCY_MS: int = 10  # Simulated latency for cache hits
    CACHE_MISS_LATENCY_MS: int = 200  # Simulated latency for origin fetches
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @property
    def edge_regions_list(self) -> List[str]:
        """Parse edge regions from comma-separated string"""
        return [r.strip() for r in self.EDGE_REGIONS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
