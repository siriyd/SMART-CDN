"""
Edge Simulator Main Application
Simulates edge nodes with Redis caching
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import time
import asyncio

from edge.config import settings
from edge.cache import EdgeCache
from edge.origin_client import OriginClient
from edge.metrics import MetricsLogger

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart CDN Edge Simulator",
    description="Edge node cache simulation service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients (will be initialized on startup)
origin_client: Optional[OriginClient] = None
metrics_logger: Optional[MetricsLogger] = None

# Edge cache instances for each region
edge_caches: Dict[str, EdgeCache] = {}


# Request/Response Models
class ContentRequest(BaseModel):
    content_id: str
    edge_id: Optional[str] = None  # If not provided, will use X-Edge-Id header


class ContentResponse(BaseModel):
    content_id: str
    edge_id: str
    is_cache_hit: bool
    response_time_ms: int
    content_data: Dict[str, Any]
    cache_ttl_seconds: Optional[int] = None


@app.on_event("startup")
async def startup_event():
    """Initialize edge caches and clients"""
    global origin_client, metrics_logger, edge_caches
    
    logger.info("Starting Edge Simulator...")
    
    # Initialize origin client
    origin_client = OriginClient()
    
    # Initialize metrics logger
    metrics_logger = MetricsLogger()
    
    # Initialize edge caches for each region
    for region in settings.edge_regions_list:
        edge_id = f"edge-{region}"
        edge_caches[edge_id] = EdgeCache(edge_id)
        logger.info(f"Initialized cache for {edge_id}")
    
    # Check origin health
    if await origin_client.check_health():
        logger.info("Origin server is healthy")
    else:
        logger.warning("Origin server health check failed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global origin_client, metrics_logger
    
    if origin_client:
        await origin_client.close()
    if metrics_logger:
        await metrics_logger.close()
    
    logger.info("Edge Simulator shutdown complete")


def get_edge_id(edge_id: Optional[str] = None, x_edge_id: Optional[str] = Header(None)) -> str:
    """Get edge ID from parameter or header, default to first region"""
    if edge_id:
        return edge_id
    if x_edge_id:
        return x_edge_id
    
    # Default to first region
    return f"edge-{settings.edge_regions_list[0]}"


def get_edge_cache(edge_id: str) -> EdgeCache:
    """Get edge cache instance"""
    if edge_id not in edge_caches:
        # Create cache on-the-fly if edge_id doesn't exist
        edge_caches[edge_id] = EdgeCache(edge_id)
        logger.info(f"Created cache for {edge_id}")
    return edge_caches[edge_id]


@app.get("/")
async def root():
    return {
        "message": "Smart CDN Edge Simulator",
        "status": "running",
        "regions": settings.edge_regions_list,
        "edges": list(edge_caches.keys())
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    redis_healthy = False
    origin_healthy = False
    
    try:
        # Check Redis
        test_cache = EdgeCache("test")
        test_cache.redis_client.ping()
        redis_healthy = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Check origin
    if origin_client:
        origin_healthy = await origin_client.check_health()
    
    return {
        "status": "healthy" if (redis_healthy and origin_healthy) else "degraded",
        "service": "edge-sim",
        "version": "1.0.0",
        "redis": "connected" if redis_healthy else "disconnected",
        "origin": "connected" if origin_healthy else "disconnected"
    }


@app.get("/api/v1/content/{content_id}")
async def get_content(
    content_id: str,
    edge_id: Optional[str] = None,
    x_edge_id: Optional[str] = Header(None, alias="X-Edge-Id")
) -> ContentResponse:
    """
    Get content from edge cache or origin.
    This is the main CDN request endpoint.
    """
    start_time = time.time()
    
    # Determine edge ID
    resolved_edge_id = get_edge_id(edge_id, x_edge_id)
    cache = get_edge_cache(resolved_edge_id)
    
    # Try cache first
    cached_content = cache.get(content_id)
    
    if cached_content:
        # Cache HIT
        response_time_ms = settings.CACHE_HIT_LATENCY_MS
        is_cache_hit = True
        content_data = {k: v for k, v in cached_content.items() if not k.startswith("_")}
        ttl = cache.get_ttl(content_id)
        
        logger.info(f"CACHE HIT: {content_id} at {resolved_edge_id} (TTL: {ttl}s)")
    else:
        # Cache MISS - fetch from origin
        if not origin_client:
            raise HTTPException(status_code=503, detail="Origin client not initialized")
        
        origin_content = await origin_client.fetch_content(content_id)
        
        if not origin_content:
            raise HTTPException(status_code=404, detail=f"Content {content_id} not found")
        
        # Store in cache
        content_data = {k: v for k, v in origin_content.items() if not k.startswith("_")}
        ttl = settings.DEFAULT_TTL_SECONDS
        cache.set(content_id, content_data, ttl_seconds=ttl)
        
        response_time_ms = settings.CACHE_MISS_LATENCY_MS
        is_cache_hit = False
        
        logger.info(f"CACHE MISS: {content_id} at {resolved_edge_id} (fetched from origin)")
    
    # Log metrics (async, don't wait)
    if metrics_logger:
        asyncio.create_task(metrics_logger.log_request(
            content_id=content_id,
            edge_id=resolved_edge_id,
            is_cache_hit=is_cache_hit,
            response_time_ms=response_time_ms
        ))
    
    return ContentResponse(
        content_id=content_id,
        edge_id=resolved_edge_id,
        is_cache_hit=is_cache_hit,
        response_time_ms=response_time_ms,
        content_data=content_data,
        cache_ttl_seconds=ttl
    )


@app.get("/api/v1/edges/{edge_id}/cache/stats")
async def get_cache_stats(edge_id: str):
    """Get cache statistics for an edge"""
    cache = get_edge_cache(edge_id)
    return cache.get_cache_stats()


@app.delete("/api/v1/edges/{edge_id}/cache/{content_id}")
async def evict_content(edge_id: str, content_id: str):
    """Evict content from edge cache"""
    cache = get_edge_cache(edge_id)
    deleted = cache.delete(content_id)
    
    if deleted:
        return {"status": "success", "message": f"Evicted {content_id} from {edge_id}"}
    else:
        return {"status": "not_found", "message": f"{content_id} not in cache at {edge_id}"}


@app.post("/api/v1/edges/{edge_id}/cache/prefetch")
async def prefetch_content(edge_id: str, content_id: str, ttl_seconds: Optional[int] = None):
    """Prefetch content into edge cache"""
    if not origin_client:
        raise HTTPException(status_code=503, detail="Origin client not initialized")
    
    cache = get_edge_cache(edge_id)
    
    # Check if already cached
    if cache.exists(content_id):
        return {
            "status": "already_cached",
            "message": f"{content_id} already in cache at {edge_id}"
        }
    
    # Fetch from origin
    origin_content = await origin_client.fetch_content(content_id)
    
    if not origin_content:
        raise HTTPException(status_code=404, detail=f"Content {content_id} not found at origin")
    
    # Store in cache
    content_data = {k: v for k, v in origin_content.items() if not k.startswith("_")}
    ttl = ttl_seconds if ttl_seconds else settings.DEFAULT_TTL_SECONDS
    success = cache.set(content_id, content_data, ttl_seconds=ttl)
    
    if success:
        return {
            "status": "success",
            "message": f"Prefetched {content_id} into {edge_id}",
            "ttl_seconds": ttl
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to cache content")


@app.put("/api/v1/edges/{edge_id}/cache/{content_id}/ttl")
async def update_ttl(edge_id: str, content_id: str, ttl_seconds: int):
    """Update TTL for cached content"""
    cache = get_edge_cache(edge_id)
    success = cache.update_ttl(content_id, ttl_seconds)
    
    if success:
        return {
            "status": "success",
            "message": f"Updated TTL for {content_id} to {ttl_seconds}s"
        }
    else:
        raise HTTPException(status_code=404, detail=f"{content_id} not found in cache")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
