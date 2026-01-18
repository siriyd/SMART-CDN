"""
Edge Nodes API Routes
Endpoints for querying edge node information
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.db.postgres import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/edges")
async def get_edges(
    db: Session = Depends(get_db)
):
    """
    Get all edge nodes.
    
    Returns:
        List of all edge nodes with their configuration
    """
    try:
        result = db.execute(text("""
            SELECT 
                edge_id,
                region,
                cache_capacity_mb,
                current_usage_mb,
                is_active,
                created_at,
                updated_at
            FROM edge_nodes
            ORDER BY region
        """))
        
        columns = result.keys()
        rows = result.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching edges: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching edges: {str(e)}")


@router.get("/edges/{edge_id}")
async def get_edge(
    edge_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specific edge node by ID.
    
    Args:
        edge_id: Edge node identifier
    
    Returns:
        Edge node details
    """
    try:
        result = db.execute(
            text("""
                SELECT 
                    edge_id,
                    region,
                    cache_capacity_mb,
                    current_usage_mb,
                    is_active,
                    created_at,
                    updated_at
                FROM edge_nodes
                WHERE edge_id = :edge_id
            """),
            {"edge_id": edge_id}
        )
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Edge node {edge_id} not found")
        
        columns = result.keys()
        data = dict(zip(columns, row))
        
        return {
            "status": "success",
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching edge {edge_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching edge: {str(e)}")


@router.get("/edges/{edge_id}/stats")
async def get_edge_stats(
    edge_id: str,
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific edge node from views.
    
    Args:
        edge_id: Edge node identifier
    
    Returns:
        Combined statistics from cache hit ratio and latency views
    """
    try:
        # Get from cache hit ratio view
        hit_ratio_result = db.execute(
            text("SELECT * FROM v_cache_hit_ratio WHERE edge_id = :edge_id"),
            {"edge_id": edge_id}
        )
        hit_ratio_row = hit_ratio_result.fetchone()
        
        # Get from latency view
        latency_result = db.execute(
            text("SELECT * FROM v_latency_by_edge WHERE edge_id = :edge_id"),
            {"edge_id": edge_id}
        )
        latency_row = latency_result.fetchone()
        
        if not hit_ratio_row and not latency_row:
            raise HTTPException(status_code=404, detail=f"No statistics found for edge {edge_id}")
        
        data = {}
        if hit_ratio_row:
            data["cache_hit_ratio"] = dict(zip(hit_ratio_result.keys(), hit_ratio_row))
        if latency_row:
            data["latency"] = dict(zip(latency_result.keys(), latency_row))
        
        return {
            "status": "success",
            "edge_id": edge_id,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching edge stats for {edge_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching edge stats: {str(e)}")
