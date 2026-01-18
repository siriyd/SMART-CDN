"""
Redis Cache Adapter for Edge Nodes
Handles cache operations with TTL support
"""
import redis
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from edge.config import settings

logger = logging.getLogger(__name__)

class EdgeCache:
    """Redis-based edge cache with TTL management"""
    
    def __init__(self, edge_id: str):
        """
        Initialize edge cache for a specific edge node.
        
        Args:
            edge_id: Edge node identifier (e.g., 'edge-us-east')
        """
        self.edge_id = edge_id
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.default_ttl = settings.DEFAULT_TTL_SECONDS
        
    def _get_cache_key(self, content_id: str) -> str:
        """Generate Redis key for content at this edge"""
        return f"edge:{self.edge_id}:content:{content_id}"
    
    def get(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Get content from cache.
        
        Args:
            content_id: Content identifier
        
        Returns:
            Content data if found, None if cache miss
        """
        try:
            cache_key = self._get_cache_key(content_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache HIT: {content_id} at {self.edge_id}")
                return data
            else:
                logger.debug(f"Cache MISS: {content_id} at {self.edge_id}")
                return None
        except redis.RedisError as e:
            logger.error(f"Redis error getting {content_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {content_id}: {e}")
            # Remove corrupted cache entry
            self.delete(content_id)
            return None
    
    def set(self, content_id: str, content_data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
        """
        Store content in cache with TTL.
        
        Args:
            content_id: Content identifier
            content_data: Content data to cache
            ttl_seconds: Time to live in seconds (uses default if None)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._get_cache_key(content_id)
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            
            # Add metadata
            cache_entry = {
                **content_data,
                "_cached_at": datetime.utcnow().isoformat(),
                "_edge_id": self.edge_id,
                "_ttl": ttl
            }
            
            serialized = json.dumps(cache_entry)
            result = self.redis_client.setex(cache_key, ttl, serialized)
            
            if result:
                logger.debug(f"Cached {content_id} at {self.edge_id} with TTL {ttl}s")
            return result
        except redis.RedisError as e:
            logger.error(f"Redis error setting {content_id}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error for {content_id}: {e}")
            return False
    
    def delete(self, content_id: str) -> bool:
        """
        Delete content from cache.
        
        Args:
            content_id: Content identifier
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache_key = self._get_cache_key(content_id)
            result = self.redis_client.delete(cache_key)
            if result:
                logger.debug(f"Deleted {content_id} from cache at {self.edge_id}")
            return bool(result)
        except redis.RedisError as e:
            logger.error(f"Redis error deleting {content_id}: {e}")
            return False
    
    def exists(self, content_id: str) -> bool:
        """
        Check if content exists in cache.
        
        Args:
            content_id: Content identifier
        
        Returns:
            True if exists, False otherwise
        """
        try:
            cache_key = self._get_cache_key(content_id)
            return bool(self.redis_client.exists(cache_key))
        except redis.RedisError as e:
            logger.error(f"Redis error checking {content_id}: {e}")
            return False
    
    def get_ttl(self, content_id: str) -> Optional[int]:
        """
        Get remaining TTL for content.
        
        Args:
            content_id: Content identifier
        
        Returns:
            Remaining TTL in seconds, None if not found
        """
        try:
            cache_key = self._get_cache_key(content_id)
            ttl = self.redis_client.ttl(cache_key)
            return ttl if ttl >= 0 else None
        except redis.RedisError as e:
            logger.error(f"Redis error getting TTL for {content_id}: {e}")
            return None
    
    def update_ttl(self, content_id: str, ttl_seconds: int) -> bool:
        """
        Update TTL for existing cache entry.
        
        Args:
            content_id: Content identifier
            ttl_seconds: New TTL in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._get_cache_key(content_id)
            if self.redis_client.exists(cache_key):
                result = self.redis_client.expire(cache_key, ttl_seconds)
                if result:
                    logger.debug(f"Updated TTL for {content_id} to {ttl_seconds}s")
                return result
            return False
        except redis.RedisError as e:
            logger.error(f"Redis error updating TTL for {content_id}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for this edge.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            pattern = f"edge:{self.edge_id}:content:*"
            keys = self.redis_client.keys(pattern)
            
            total_size = 0
            for key in keys:
                try:
                    value = self.redis_client.get(key)
                    if value:
                        total_size += len(value)
                except:
                    pass
            
            return {
                "edge_id": self.edge_id,
                "cached_items": len(keys),
                "estimated_size_bytes": total_size,
                "estimated_size_mb": round(total_size / (1024 * 1024), 2),
                "capacity_mb": settings.EDGE_CACHE_CAPACITY_MB
            }
        except redis.RedisError as e:
            logger.error(f"Redis error getting cache stats: {e}")
            return {
                "edge_id": self.edge_id,
                "cached_items": 0,
                "estimated_size_bytes": 0,
                "estimated_size_mb": 0,
                "capacity_mb": settings.EDGE_CACHE_CAPACITY_MB,
                "error": str(e)
            }
    
    def clear_cache(self) -> int:
        """
        Clear all cached content for this edge.
        
        Returns:
            Number of keys deleted
        """
        try:
            pattern = f"edge:{self.edge_id}:content:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} items from cache at {self.edge_id}")
                return deleted
            return 0
        except redis.RedisError as e:
            logger.error(f"Redis error clearing cache: {e}")
            return 0
