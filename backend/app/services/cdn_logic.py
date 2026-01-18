"""
CDN Logic Service
Applies AI decisions to edge caches via edge simulator
"""
import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class CDNLogicService:
    """Service for applying cache decisions to edge nodes"""
    
    def __init__(self, edge_sim_url: str = "http://localhost:8002"):
        """
        Initialize CDN logic service.
        
        Args:
            edge_sim_url: Edge simulator base URL
        """
        self.edge_sim_url = edge_sim_url
        self.client = httpx.AsyncClient(
            base_url=edge_sim_url,
            timeout=10.0
        )
    
    async def apply_prefetch(
        self,
        content_id: str,
        edge_id: str,
        ttl_seconds: int
    ) -> bool:
        """
        Apply prefetch decision to edge cache.
        
        Args:
            content_id: Content ID to prefetch
            edge_id: Edge ID to prefetch to
            ttl_seconds: TTL for cached content
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.post(
                f"/api/v1/edges/{edge_id}/cache/prefetch",
                params={"content_id": content_id, "ttl_seconds": ttl_seconds},
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Prefetched {content_id} to {edge_id}")
                return True
            else:
                logger.warning(f"Prefetch failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error applying prefetch: {e}")
            return False
    
    async def apply_eviction(
        self,
        content_id: str,
        edge_id: str
    ) -> bool:
        """
        Apply eviction decision to edge cache.
        
        Args:
            content_id: Content ID to evict
            edge_id: Edge ID to evict from
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.delete(
                f"/api/v1/edges/{edge_id}/cache/{content_id}",
                timeout=10.0
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Evicted {content_id} from {edge_id}")
                return True
            else:
                logger.warning(f"Eviction failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error applying eviction: {e}")
            return False
    
    async def apply_ttl_update(
        self,
        content_id: str,
        edge_id: str,
        ttl_seconds: int
    ) -> bool:
        """
        Apply TTL update decision to edge cache.
        
        Args:
            content_id: Content ID
            edge_id: Edge ID
            ttl_seconds: New TTL
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.put(
                f"/api/v1/edges/{edge_id}/cache/{content_id}/ttl",
                params={"ttl_seconds": ttl_seconds},
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"Updated TTL for {content_id} at {edge_id} to {ttl_seconds}s")
                return True
            else:
                logger.warning(f"TTL update failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error applying TTL update: {e}")
            return False
    
    async def apply_decisions(
        self,
        decisions: Dict[str, Any],
        experiment_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Apply all AI decisions to edge caches.
        
        Args:
            decisions: AI decision response
            experiment_id: Optional experiment ID
        
        Returns:
            Summary of applied decisions
        """
        prefetch_plan = decisions.get("prefetch_plan", [])
        eviction_plan = decisions.get("eviction_plan", [])
        ttl_updates = decisions.get("ttl_updates", [])
        
        results = {
            "prefetch": {"success": 0, "failed": 0},
            "eviction": {"success": 0, "failed": 0},
            "ttl_updates": {"success": 0, "failed": 0}
        }
        
        # Apply prefetch decisions
        for item in prefetch_plan:
            content_id = item.get("content_id")
            target_edges = item.get("target_edges", [])
            ttl_seconds = item.get("ttl_seconds", 3600)
            
            for edge_id in target_edges:
                if await self.apply_prefetch(content_id, edge_id, ttl_seconds):
                    results["prefetch"]["success"] += 1
                else:
                    results["prefetch"]["failed"] += 1
        
        # Apply eviction decisions
        for item in eviction_plan:
            content_id = item.get("content_id")
            edge_id = item.get("edge_id")
            
            if await self.apply_eviction(content_id, edge_id):
                results["eviction"]["success"] += 1
            else:
                results["eviction"]["failed"] += 1
        
        # Apply TTL updates
        for item in ttl_updates:
            content_id = item.get("content_id")
            edge_id = item.get("edge_id")
            ttl_seconds = item.get("new_ttl_seconds", 3600)
            
            if await self.apply_ttl_update(content_id, edge_id, ttl_seconds):
                results["ttl_updates"]["success"] += 1
            else:
                results["ttl_updates"]["failed"] += 1
        
        logger.info(f"Applied decisions: {results}")
        return results
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
