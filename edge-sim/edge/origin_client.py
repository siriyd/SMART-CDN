"""
Origin Server Client
Fetches content from backend origin server
"""
import httpx
import logging
import time
from typing import Dict, Any, Optional

from edge.config import settings

logger = logging.getLogger(__name__)

class OriginClient:
    """Client for fetching content from origin server"""
    
    def __init__(self):
        """Initialize origin client"""
        self.base_url = settings.ORIGIN_SERVER_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0
        )
    
    async def fetch_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch content from origin server.
        
        Args:
            content_id: Content identifier
        
        Returns:
            Content data if found, None otherwise
        """
        try:
            start_time = time.time()
            
            # Simulate origin fetch endpoint
            # In real implementation, this would be: /api/v1/content/{content_id}
            response = await self.client.get(f"/api/v1/content/{content_id}")
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                content_data = data.get("data", {})
                logger.info(f"Fetched {content_id} from origin in {elapsed_ms}ms")
                return {
                    **content_data,
                    "_origin_fetch_time_ms": elapsed_ms,
                    "_fetched_at": time.time()
                }
            elif response.status_code == 404:
                logger.warning(f"Content {content_id} not found at origin")
                return None
            else:
                logger.error(f"Origin fetch failed for {content_id}: {response.status_code}")
                return None
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {content_id} from origin")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {content_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {content_id}: {e}")
            return None
    
    async def check_health(self) -> bool:
        """
        Check if origin server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Origin health check failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
