"""
Caching Policy Engine
Makes prefetch, eviction, and TTL decisions based on predictions
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CachingPolicy:
    """Caching policy engine for making cache decisions"""
    
    def __init__(
        self,
        prefetch_threshold: int = 2,  # Lowered from 5 for better sensitivity
        eviction_threshold: int = 0,
        min_ttl: int = 60,
        max_ttl: int = 86400
    ):
        """
        Initialize policy engine.
        
        Args:
            prefetch_threshold: Minimum predicted requests to trigger prefetch
            eviction_threshold: Maximum predicted requests below which to evict
            min_ttl: Minimum TTL in seconds
            max_ttl: Maximum TTL in seconds
        """
        self.prefetch_threshold = prefetch_threshold
        self.eviction_threshold = eviction_threshold
        self.min_ttl = min_ttl
        self.max_ttl = max_ttl
    
    def make_prefetch_plan(
        self,
        popularity_forecast: List[Dict[str, Any]],
        edge_constraints: List[Dict[str, Any]],
        content_metadata: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate prefetch plan based on popularity predictions.
        
        Args:
            popularity_forecast: List of popularity predictions
            edge_constraints: Edge cache constraints (capacity, usage, etc.)
            content_metadata: Content metadata (size, type, etc.)
        
        Returns:
            List of prefetch decisions
        """
        prefetch_plan = []
        
        # Create metadata lookup
        metadata_lookup = {
            str(item.get("content_id", "")): item
            for item in content_metadata
        }
        
        # Create edge constraints lookup
        edge_lookup = {
            item.get("edge_id", ""): item
            for item in edge_constraints
        }
        
        # Sort forecasts by predicted requests (descending)
        sorted_forecasts = sorted(
            popularity_forecast,
            key=lambda x: x.get("predicted_requests_next_window", 0),
            reverse=True
        )
        
        for forecast in sorted_forecasts:
            content_id = forecast["content_id"]
            predicted_requests = forecast.get("predicted_requests_next_window", 0)
            confidence = forecast.get("confidence", 0.0)
            
            # Only prefetch if above threshold and confidence is reasonable
            # Lowered confidence threshold from 0.3 to 0.2 for better sensitivity
            if predicted_requests < self.prefetch_threshold or confidence < 0.2:
                continue
            
            metadata = metadata_lookup.get(content_id, {})
            content_size_kb = metadata.get("size_kb", 0)
            
            # Determine target edges (all active edges by default)
            target_edges = []
            for edge_id, edge_info in edge_lookup.items():
                if not edge_id:
                    continue
                
                # Check if edge has capacity
                capacity_mb = edge_info.get("cache_capacity_mb", 100)
                current_usage_mb = edge_info.get("current_usage_mb", 0)
                free_space_mb = capacity_mb - current_usage_mb
                
                # Check if content fits (with some margin)
                content_size_mb = content_size_kb / 1024
                if content_size_mb < free_space_mb * 0.8:  # 80% of free space
                    target_edges.append(edge_id)
            
            if not target_edges:
                logger.debug(f"Skipping prefetch for {content_id}: no edge capacity")
                continue
            
            # Calculate TTL based on predicted popularity
            # Higher popularity = longer TTL
            base_ttl = self.min_ttl
            if predicted_requests > 50:
                ttl = self.max_ttl
            elif predicted_requests > 20:
                ttl = int(self.max_ttl * 0.7)
            elif predicted_requests > 10:
                ttl = int(self.max_ttl * 0.5)
            else:
                ttl = int(self.max_ttl * 0.3)
            
            ttl = max(self.min_ttl, min(self.max_ttl, ttl))
            
            # Calculate priority (0-100)
            priority = min(100, int(predicted_requests * 2))
            
            prefetch_plan.append({
                "content_id": content_id,
                "target_edges": target_edges,
                "ttl_seconds": ttl,
                "priority": priority
            })
        
        logger.info(f"Generated {len(prefetch_plan)} prefetch decisions")
        return prefetch_plan
    
    def make_prefetch_plan_with_fallback(
        self,
        popularity_forecast: List[Dict[str, Any]],
        edge_constraints: List[Dict[str, Any]],
        content_metadata: List[Dict[str, Any]],
        request_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate prefetch plan with fallback mechanism.
        If no decisions are generated but we have request data, prefetch the most requested content.
        This ensures at least one decision is generated when there's traffic data.
        
        Args:
            popularity_forecast: List of popularity predictions
            edge_constraints: Edge cache constraints
            content_metadata: Content metadata
            request_logs: Original request logs (for fallback)
        
        Returns:
            List of prefetch decisions (at least one if we have request data)
        """
        # Try normal prefetch plan first
        prefetch_plan = self.make_prefetch_plan(
            popularity_forecast=popularity_forecast,
            edge_constraints=edge_constraints,
            content_metadata=content_metadata
        )
        
        # Fallback: if no prefetch decisions but we have request logs, prefetch most requested content
        if len(prefetch_plan) == 0 and len(request_logs) > 0:
            logger.info("No prefetch decisions generated; using fallback: prefetch most requested content")
            
            # Count requests per content_id
            from collections import Counter
            content_request_counts = Counter()
            for log in request_logs:
                content_id = str(log.get("content_id", ""))
                if content_id:
                    content_request_counts[content_id] += 1
            
            if content_request_counts:
                # Get most requested content
                most_requested_id, request_count = content_request_counts.most_common(1)[0]
                
                # Create metadata lookup
                metadata_lookup = {
                    str(item.get("content_id", "")): item
                    for item in content_metadata
                }
                
                # Create edge constraints lookup
                edge_lookup = {
                    item.get("edge_id", ""): item
                    for item in edge_constraints
                }
                
                metadata = metadata_lookup.get(most_requested_id, {})
                content_size_kb = metadata.get("size_kb", 100)  # Default 100KB if unknown
                
                # Determine target edges (all active edges with capacity)
                target_edges = []
                for edge_id, edge_info in edge_lookup.items():
                    if not edge_id:
                        continue
                    
                    capacity_mb = edge_info.get("cache_capacity_mb", 100)
                    current_usage_mb = edge_info.get("current_usage_mb", 0)
                    free_space_mb = capacity_mb - current_usage_mb
                    
                    content_size_mb = content_size_kb / 1024
                    if content_size_mb < free_space_mb * 0.8:
                        target_edges.append(edge_id)
                
                if target_edges:
                    # Generate prefetch decision for most requested content
                    # Use moderate TTL (30% of max)
                    ttl = int(self.max_ttl * 0.3)
                    ttl = max(self.min_ttl, min(self.max_ttl, ttl))
                    
                    prefetch_plan.append({
                        "content_id": most_requested_id,
                        "target_edges": target_edges,
                        "ttl_seconds": ttl,
                        "priority": min(100, request_count * 2)  # Priority based on request count
                    })
                    
                    logger.info(
                        f"Fallback prefetch: {most_requested_id} "
                        f"(requested {request_count} times) to {len(target_edges)} edge(s)"
                    )
        
        return prefetch_plan
    
    def make_eviction_plan(
        self,
        popularity_forecast: List[Dict[str, Any]],
        edge_constraints: List[Dict[str, Any]],
        cache_state: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate eviction plan for low-priority cached content.
        
        Args:
            popularity_forecast: Popularity predictions
            edge_constraints: Edge cache constraints
            cache_state: Current cache state (optional)
        
        Returns:
            List of eviction decisions
        """
        eviction_plan = []
        
        # Create forecast lookup
        forecast_lookup = {
            item.get("content_id", ""): item
            for item in popularity_forecast
        }
        
        # If cache state provided, use it; otherwise evict based on low predictions
        if cache_state:
            for cache_entry in cache_state:
                content_id = cache_entry.get("content_id", "")
                edge_id = cache_entry.get("edge_id", "")
                
                forecast = forecast_lookup.get(content_id, {})
                predicted_requests = forecast.get("predicted_requests_next_window", 0)
                
                # Evict if predicted requests are very low
                if predicted_requests <= self.eviction_threshold:
                    eviction_plan.append({
                        "edge_id": edge_id,
                        "content_id": content_id,
                        "reason": f"Low predicted popularity ({predicted_requests} requests)",
                        "priority": 100 - predicted_requests  # Higher priority for lower popularity
                    })
        else:
            # Evict based on forecasts alone
            for forecast in popularity_forecast:
                content_id = forecast["content_id"]
                predicted_requests = forecast.get("predicted_requests_next_window", 0)
                
                if predicted_requests <= self.eviction_threshold:
                    # Evict from all edges (if we had cache state, we'd be more specific)
                    for edge_constraint in edge_constraints:
                        edge_id = edge_constraint.get("edge_id", "")
                        if edge_id:
                            eviction_plan.append({
                                "edge_id": edge_id,
                                "content_id": content_id,
                                "reason": f"Low predicted popularity ({predicted_requests} requests)",
                                "priority": 100 - predicted_requests
                            })
        
        logger.info(f"Generated {len(eviction_plan)} eviction decisions")
        return eviction_plan
    
    def make_ttl_updates(
        self,
        popularity_forecast: List[Dict[str, Any]],
        cache_state: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate TTL update decisions based on popularity changes.
        
        Args:
            popularity_forecast: Popularity predictions
            cache_state: Current cache state (optional)
        
        Returns:
            List of TTL update decisions
        """
        ttl_updates = []
        
        if not cache_state:
            return ttl_updates
        
        # Create forecast lookup
        forecast_lookup = {
            item.get("content_id", ""): item
            for item in popularity_forecast
        }
        
        for cache_entry in cache_state:
            content_id = cache_entry.get("content_id", "")
            edge_id = cache_entry.get("edge_id", "")
            current_ttl = cache_entry.get("ttl_seconds", self.min_ttl)
            
            forecast = forecast_lookup.get(content_id, {})
            predicted_requests = forecast.get("predicted_requests_next_window", 0)
            
            # Calculate new TTL based on predicted popularity
            if predicted_requests > 50:
                new_ttl = self.max_ttl
            elif predicted_requests > 20:
                new_ttl = int(self.max_ttl * 0.7)
            elif predicted_requests > 10:
                new_ttl = int(self.max_ttl * 0.5)
            else:
                new_ttl = int(self.max_ttl * 0.3)
            
            new_ttl = max(self.min_ttl, min(self.max_ttl, new_ttl))
            
            # Only update if TTL changed significantly (>20%)
            if abs(new_ttl - current_ttl) > (current_ttl * 0.2):
                ttl_updates.append({
                    "edge_id": edge_id,
                    "content_id": content_id,
                    "new_ttl_seconds": new_ttl
                })
        
        logger.info(f"Generated {len(ttl_updates)} TTL update decisions")
        return ttl_updates
