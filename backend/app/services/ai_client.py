"""
AI Engine Client
Client for calling AI engine and applying decisions
"""
import httpx
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# Try to import SQLAlchemy Row types (for safety, though data should already be dicts)
try:
    from sqlalchemy.engine import Row, RowMapping
except ImportError:
    # SQLAlchemy not available or different version - use duck typing instead
    Row = None
    RowMapping = None


class AIClient:
    """Client for AI engine service"""
    
    def __init__(self):
        """Initialize AI client"""
        self.base_url = settings.AI_ENGINE_URL
        logger.info(f"AI Engine URL configured: {self.base_url}")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0
        )

    def _serialize(self, obj: Any) -> Any:
        """
        Recursively serialize objects to JSON-serializable format.
        Handles datetime, dict, list, and SQLAlchemy Row objects (if present).
        
        Args:
            obj: Object to serialize
        
        Returns:
            JSON-serializable object
        """
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle SQLAlchemy Row/RowMapping (if imported and present)
        # Note: routes_ai.py already converts rows to dicts, but this is a safety check
        if Row is not None and RowMapping is not None:
            if isinstance(obj, (Row, RowMapping)):
                return {k: self._serialize(v) for k, v in obj.items()}
        else:
            # Duck typing fallback: if it has .items() and isn't a dict, treat as row-like
            if hasattr(obj, 'items') and not isinstance(obj, dict):
                try:
                    return {k: self._serialize(v) for k, v in obj.items()}
                except (AttributeError, TypeError):
                    pass  # Not actually row-like, continue to other checks
        
        # Handle dictionaries
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        
        # Handle lists
        if isinstance(obj, list):
            return [self._serialize(item) for item in obj]
        
        # Return primitive types as-is (int, float, str, bool, None)
        return obj

    async def get_decisions(
        self,
        request_logs: List[Dict[str, Any]],
        content_metadata: List[Dict[str, Any]],
        edge_constraints: List[Dict[str, Any]],
        time_window_minutes: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Get caching decisions from AI engine.
        
        Args:
            request_logs: Recent request logs
            content_metadata: Content metadata
            edge_constraints: Edge cache constraints
            time_window_minutes: Prediction time window
        
        Returns:
            AI decision response or None if error
            Note: Empty but valid responses (with empty lists) are accepted as success
        """
        try:
            request_data = {
                "request_logs": self._serialize(request_logs),
                "content_metadata": self._serialize(content_metadata),
                "edge_constraints": self._serialize(edge_constraints),
                "time_window_minutes": time_window_minutes
            }
            
            logger.debug(f"Calling AI engine at {self.base_url}/decide with {len(request_logs)} request logs")
            
            # Serialize the entire request_data to ensure all nested structures are JSON-serializable
            # (components are already serialized, but this ensures the top-level dict is also handled)
            serialized_data = self._serialize(request_data)
            response = await self.client.post(
                "/decide",
                json=serialized_data,
                timeout=30.0
            )
            
            # Log response status for debugging
            logger.debug(f"AI engine response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    # Parse JSON response
                    decisions = response.json()
                    
                    # Validate that we got a dict (even if empty)
                    if not isinstance(decisions, dict):
                        logger.error(f"AI engine returned non-dict response: {type(decisions)}")
                        logger.error(f"Response content: {response.text[:500]}")
                        return None
                    
                    # Empty but valid responses are acceptable
                    # (e.g., no predictions when there's no data)
                    logger.info(
                        f"AI decisions received: "
                        f"{len(decisions.get('popularity_forecast', []))} forecasts, "
                        f"{len(decisions.get('prefetch_plan', []))} prefetch, "
                        f"{len(decisions.get('eviction_plan', []))} evict, "
                        f"{len(decisions.get('ttl_updates', []))} TTL updates"
                    )
                    
                    return decisions
                    
                except ValueError as e:
                    # JSON parsing error
                    logger.error(f"Failed to parse AI engine JSON response: {e}")
                    logger.error(f"Response status: {response.status_code}")
                    logger.error(f"Response headers: {dict(response.headers)}")
                    logger.error(f"Response text (first 500 chars): {response.text[:500]}")
                    return None
            else:
                # Non-200 status code
                logger.error(f"AI engine returned status {response.status_code}")
                try:
                    error_detail = response.json()
                    logger.error(f"Error response: {error_detail}")
                except:
                    logger.error(f"Error response text: {response.text[:500]}")
                return None
                
        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling AI engine: {e}")
            logger.error(f"Request URL: {self.base_url}/decide")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error calling AI engine: {e}")
            logger.error(f"Request URL: {self.base_url}/decide")
            logger.error(f"Error type: {type(e).__name__}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling AI engine: {e}", exc_info=True)
            logger.error(f"Error type: {type(e).__name__}")
            return None
    
    async def check_health(self) -> bool:
        """
        Check if AI engine is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"AI engine health check failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
