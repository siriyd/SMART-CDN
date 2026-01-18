"""
Baseline Caching Service
Implements LRU/LFU caching strategies when AI is disabled
"""
import redis
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timezone, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaselineCacheService:
    """
    Baseline caching service using LRU (Least Recently Used) and LFU (Least Frequently Used) strategies.
    Used when AI is disabled.
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour default TTL
    
    def get_cache_key(self, edge_id: str, content_id: str) -> str:
        """Generate Redis key for cache entry"""
        return f"edge:{edge_id}:content:{content_id}"
    
    def get_access_key(self, edge_id: str, content_id: str) -> str:
        """Generate Redis key for access tracking (LRU)"""
        return f"edge:{edge_id}:access:{content_id}"
    
    def get_frequency_key(self, edge_id: str, content_id: str) -> str:
        """Generate Redis key for frequency tracking (LFU)"""
        return f"edge:{edge_id}:freq:{content_id}"
    
    def cache_content(
        self,
        edge_id: str,
        content_id: str,
        content_data: str,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Cache content using baseline strategy.
        
        Args:
            edge_id: Edge node ID
            content_id: Content ID
            content_data: Content data to cache
            ttl_seconds: Optional TTL (uses default if not provided)
        
        Returns:
            True if cached successfully
        """
        try:
            cache_key = self.get_cache_key(edge_id, content_id)
            access_key = self.get_access_key(edge_id, content_id)
            freq_key = self.get_frequency_key(edge_id, content_id)
            
            ttl = ttl_seconds or self.default_ttl
            
            # Store content
            self.redis_client.setex(cache_key, ttl, content_data)
            
            # Track access time (for LRU)
            self.redis_client.setex(access_key, ttl, str(datetime.now(timezone.utc).timestamp()))
            
            # Track frequency (for LFU) - initialize to 1
            self.redis_client.setex(freq_key, ttl, "1")
            
            return True
        except Exception as e:
            logger.error(f"Error caching content: {e}", exc_info=True)
            return False
    
    def get_content(self, edge_id: str, content_id: str) -> Optional[str]:
        """
        Get content from cache and update access tracking.
        
        Args:
            edge_id: Edge node ID
            content_id: Content ID
        
        Returns:
            Cached content or None if not found
        """
        try:
            cache_key = self.get_cache_key(edge_id, content_id)
            access_key = self.get_access_key(edge_id, content_id)
            freq_key = self.get_frequency_key(edge_id, content_id)
            
            content = self.redis_client.get(cache_key)
            
            if content:
                # Update access time (LRU)
                ttl = self.redis_client.ttl(cache_key)
                if ttl > 0:
                    self.redis_client.setex(
                        access_key,
                        ttl,
                        str(datetime.now(timezone.utc).timestamp())
                    )
                    
                    # Increment frequency (LFU)
                    current_freq = self.redis_client.get(freq_key)
                    if current_freq:
                        new_freq = int(current_freq) + 1
                        self.redis_client.setex(freq_key, ttl, str(new_freq))
                
                return content
            
            return None
        except Exception as e:
            logger.error(f"Error getting content from cache: {e}", exc_info=True)
            return None
    
    def evict_lru(self, edge_id: str, max_items: int = 10) -> List[str]:
        """
        Evict least recently used items (LRU strategy).
        
        Args:
            edge_id: Edge node ID
            max_items: Maximum number of items to evict
        
        Returns:
            List of evicted content IDs
        """
        try:
            # Get all access keys for this edge
            pattern = f"edge:{edge_id}:access:*"
            keys = self.redis_client.keys(pattern)
            
            if len(keys) <= max_items:
                return []
            
            # Get access times and sort by least recent
            access_times = []
            for key in keys:
                content_id = key.split(":")[-1]
                access_time_str = self.redis_client.get(key)
                if access_time_str:
                    try:
                        access_time = float(access_time_str)
                        access_times.append((access_time, content_id))
                    except:
                        pass
            
            # Sort by access time (oldest first)
            access_times.sort(key=lambda x: x[0])
            
            # Evict oldest items
            evicted = []
            for access_time, content_id in access_times[:max_items]:
                cache_key = self.get_cache_key(edge_id, content_id)
                access_key = self.get_access_key(edge_id, content_id)
                freq_key = self.get_frequency_key(edge_id, content_id)
                
                self.redis_client.delete(cache_key)
                self.redis_client.delete(access_key)
                self.redis_client.delete(freq_key)
                evicted.append(content_id)
            
            return evicted
        except Exception as e:
            logger.error(f"Error evicting LRU items: {e}", exc_info=True)
            return []
    
    def evict_lfu(self, edge_id: str, max_items: int = 10) -> List[str]:
        """
        Evict least frequently used items (LFU strategy).
        
        Args:
            edge_id: Edge node ID
            max_items: Maximum number of items to evict
        
        Returns:
            List of evicted content IDs
        """
        try:
            # Get all frequency keys for this edge
            pattern = f"edge:{edge_id}:freq:*"
            keys = self.redis_client.keys(pattern)
            
            if len(keys) <= max_items:
                return []
            
            # Get frequencies and sort by least frequent
            frequencies = []
            for key in keys:
                content_id = key.split(":")[-1]
                freq_str = self.redis_client.get(key)
                if freq_str:
                    try:
                        freq = int(freq_str)
                        frequencies.append((freq, content_id))
                    except:
                        pass
            
            # Sort by frequency (lowest first)
            frequencies.sort(key=lambda x: x[0])
            
            # Evict least frequent items
            evicted = []
            for freq, content_id in frequencies[:max_items]:
                cache_key = self.get_cache_key(edge_id, content_id)
                access_key = self.get_access_key(edge_id, content_id)
                freq_key = self.get_frequency_key(edge_id, content_id)
                
                self.redis_client.delete(cache_key)
                self.redis_client.delete(access_key)
                self.redis_client.delete(freq_key)
                evicted.append(content_id)
            
            return evicted
        except Exception as e:
            logger.error(f"Error evicting LFU items: {e}", exc_info=True)
            return []
    
    def get_cache_stats(self, edge_id: str) -> Dict[str, any]:
        """
        Get cache statistics for an edge.
        
        Args:
            edge_id: Edge node ID
        
        Returns:
            Cache statistics dictionary
        """
        try:
            pattern = f"edge:{edge_id}:content:*"
            keys = self.redis_client.keys(pattern)
            
            total_items = len(keys)
            total_size = 0
            
            for key in keys:
                content = self.redis_client.get(key)
                if content:
                    total_size += len(content.encode('utf-8'))
            
            return {
                "total_items": total_items,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}", exc_info=True)
            return {
                "total_items": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0
            }

