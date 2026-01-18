"""
Metrics API Routes
Endpoints for querying metrics from database tables
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Optional
import logging

from app.db.postgres import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics/summary")
async def get_metrics_summary(
    db: Session = Depends(get_db)
):
    """
    Get overall metrics summary.
    
    Returns:
        {
            "total_requests": count from requests table,
            "cache_hit_ratio": hits/total * 100,
            "avg_latency_ms": average response_time_ms,
            "active_edges": count from edge_nodes where is_active=true
        }
    """
    try:
        # Total requests count
        total_requests_result = db.execute(text("SELECT COUNT(*) FROM requests"))
        total_requests = total_requests_result.scalar() or 0
        
        # Cache hit ratio
        hit_stats_result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_cache_hit = true THEN 1 ELSE 0 END) as hits
            FROM requests
        """))
        hit_stats = hit_stats_result.fetchone()
        total = hit_stats[0] or 0
        hits = hit_stats[1] or 0
        cache_hit_ratio = (hits / total * 100) if total > 0 else 0.0
        
        # Average latency
        avg_latency_result = db.execute(text("""
            SELECT AVG(response_time_ms) 
            FROM requests
        """))
        avg_latency_ms = avg_latency_result.scalar() or 0.0
        
        # Active edges count
        active_edges_result = db.execute(text("""
            SELECT COUNT(*) 
            FROM edge_nodes 
            WHERE is_active = true
        """))
        active_edges = active_edges_result.scalar() or 0
        
        return {
            "total_requests": total_requests,
            "cache_hit_ratio": round(cache_hit_ratio, 2),
            "avg_latency_ms": round(avg_latency_ms, 2),
            "active_edges": active_edges
        }
    except Exception as e:
        logger.error(f"Error fetching metrics summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching metrics summary: {str(e)}")


@router.get("/metrics/cache-hit-ratio")
async def get_cache_hit_ratio(
    db: Session = Depends(get_db)
):
    """
    Get cache hit ratio statistics by edge.
    
    Returns:
        List of edge nodes with cache hit ratio metrics:
        [
            {"edge_id": "...", "hit_ratio": X, "hits": Y, "misses": Z, ...}
        ]
    """
    try:
        result = db.execute(text("""
            SELECT 
                r.edge_id,
                e.region,
                COUNT(*) as total_requests,
                SUM(CASE WHEN r.is_cache_hit = true THEN 1 ELSE 0 END) as hits,
                SUM(CASE WHEN r.is_cache_hit = false THEN 1 ELSE 0 END) as misses,
                AVG(r.response_time_ms) as avg_response_time_ms,
                AVG(CASE WHEN r.is_cache_hit = true THEN r.response_time_ms END) as avg_hit_latency_ms,
                AVG(CASE WHEN r.is_cache_hit = false THEN r.response_time_ms END) as avg_miss_latency_ms
            FROM requests r
            LEFT JOIN edge_nodes e ON r.edge_id = e.edge_id
            GROUP BY r.edge_id, e.region
            ORDER BY total_requests DESC
        """))
        
        data = []
        for row in result:
            total = row[2] or 0
            hits = row[3] or 0
            misses = row[4] or 0
            hit_ratio = (hits / total * 100) if total > 0 else 0.0
            
            data.append({
                "edge_id": row[0],
                "region": row[1] or row[0],  # Fallback to edge_id if region is null
                "hit_ratio": round(hit_ratio, 2),
                "hit_ratio_percent": round(hit_ratio, 2),  # For backward compatibility
                "hits": hits,
                "cache_hits": hits,  # For backward compatibility
                "misses": misses,
                "cache_misses": misses,  # For backward compatibility
                "total_requests": total,
                "avg_response_time_ms": round(float(row[5] or 0), 2),
                "avg_hit_latency_ms": round(float(row[6] or 0), 2),
                "avg_miss_latency_ms": round(float(row[7] or 0), 2)
            })
        
        return data
    except Exception as e:
        logger.error(f"Error fetching cache hit ratio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching cache hit ratio: {str(e)}")


@router.get("/metrics/popularity")
async def get_content_popularity(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get top content by request count.
    
    Args:
        limit: Maximum number of results to return (1-100)
    
    Returns:
        List of content items with popularity metrics:
        [
            {"content_id": "...", "total_requests": X, "hit_ratio": Y}
        ]
    """
    try:
        result = db.execute(text("""
            SELECT 
                content_id,
                COUNT(*) as total_requests,
                SUM(CASE WHEN is_cache_hit = true THEN 1 ELSE 0 END) as hits,
                SUM(CASE WHEN is_cache_hit = false THEN 1 ELSE 0 END) as misses
            FROM requests
            GROUP BY content_id
            ORDER BY total_requests DESC
            LIMIT :limit
        """), {"limit": limit})
        
        data = []
        for row in result:
            total = row[1] or 0
            hits = row[2] or 0
            misses = row[3] or 0
            hit_ratio = (hits / total * 100) if total > 0 else 0.0
            
            data.append({
                "content_id": row[0],
                "total_requests": total,
                "hit_ratio": round(hit_ratio, 2),
                "hits": hits,
                "misses": misses
            })
        
        return data
    except Exception as e:
        logger.error(f"Error fetching content popularity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching content popularity: {str(e)}")


@router.get("/metrics/latency")
async def get_latency_metrics(
    db: Session = Depends(get_db)
):
    """
    Get latency comparison between cache hits and misses.
    
    Returns:
        {
            "cache_hit_avg": average latency for cache hits,
            "cache_miss_avg": average latency for cache misses,
            "data": [list of edge-specific latency data for backward compatibility]
        }
    """
    try:
        # Overall averages
        result = db.execute(text("""
            SELECT 
                AVG(CASE WHEN is_cache_hit = true THEN response_time_ms END) as hit_avg,
                AVG(CASE WHEN is_cache_hit = false THEN response_time_ms END) as miss_avg
            FROM requests
        """))
        
        row = result.fetchone()
        cache_hit_avg = float(row[0]) if row[0] is not None else 0.0
        cache_miss_avg = float(row[1]) if row[1] is not None else 0.0
        
        # Per-edge latency data (for backward compatibility with frontend)
        edge_result = db.execute(text("""
            SELECT 
                r.edge_id,
                e.region,
                AVG(r.response_time_ms) as avg_response_time_ms,
                AVG(CASE WHEN r.is_cache_hit = true THEN r.response_time_ms END) as avg_hit_latency_ms,
                AVG(CASE WHEN r.is_cache_hit = false THEN r.response_time_ms END) as avg_miss_latency_ms
            FROM requests r
            LEFT JOIN edge_nodes e ON r.edge_id = e.edge_id
            GROUP BY r.edge_id, e.region
            ORDER BY r.edge_id
        """))
        
        edge_data = []
        for edge_row in edge_result:
            edge_data.append({
                "edge_id": edge_row[0],
                "region": edge_row[1] or edge_row[0],
                "avg_response_time_ms": round(float(edge_row[2] or 0), 2),
                "avg_hit_latency_ms": round(float(edge_row[3] or 0), 2),
                "avg_miss_latency_ms": round(float(edge_row[4] or 0), 2)
            })
        
        return {
            "cache_hit_avg": round(cache_hit_avg, 2),
            "cache_miss_avg": round(cache_miss_avg, 2),
            "data": edge_data  # For backward compatibility
        }
    except Exception as e:
        logger.error(f"Error fetching latency metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching latency metrics: {str(e)}")


# Keep backward compatibility with old endpoint name
@router.get("/metrics/content-popularity")
async def get_content_popularity_legacy(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Legacy endpoint for content popularity (backward compatibility).
    Redirects to /metrics/popularity
    """
    return await get_content_popularity(limit=limit, db=db)
