"""
Metrics Logging Service
Logs request metrics to backend database
"""
import httpx
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from edge.config import settings

logger = logging.getLogger(__name__)

class MetricsLogger:
    """Logs request metrics to backend API"""
    
    def __init__(self):
        """Initialize metrics logger"""
        self.backend_url = settings.ORIGIN_SERVER_URL
        self.client = httpx.AsyncClient(
            base_url=self.backend_url,
            timeout=10.0
        )
    
    async def log_request(
        self,
        content_id: str,
        edge_id: str,
        is_cache_hit: bool,
        response_time_ms: int,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        experiment_id: Optional[int] = None
    ) -> bool:
        """
        Log request to backend database.
        
        Args:
            content_id: Content identifier
            edge_id: Edge node identifier
            is_cache_hit: Whether request was served from cache
            response_time_ms: Response time in milliseconds
            user_ip: User IP address (optional)
            user_agent: User agent string (optional)
            experiment_id: Experiment ID (optional)
        
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            request_data = {
                "content_id": content_id,
                "edge_id": edge_id,
                "is_cache_hit": is_cache_hit,
                "response_time_ms": response_time_ms,
                "request_timestamp": datetime.utcnow().isoformat(),
                "user_ip": user_ip,
                "user_agent": user_agent,
                "experiment_id": experiment_id
            }
            
            # In Part 5, we'll create the actual endpoint
            # For now, we'll use a placeholder endpoint
            response = await self.client.post(
                "/api/v1/requests/log",
                json=request_data,
                timeout=5.0
            )
            
            if response.status_code in [200, 201]:
                logger.debug(f"Logged request: {content_id} at {edge_id} (hit={is_cache_hit})")
                return True
            else:
                logger.warning(f"Failed to log request: {response.status_code}")
                return False
        except httpx.TimeoutException:
            logger.warning(f"Timeout logging request for {content_id}")
            return False
        except httpx.RequestError as e:
            logger.warning(f"Request error logging metrics: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging metrics: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
