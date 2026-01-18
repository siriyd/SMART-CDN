"""
Content API Routes
Endpoints for querying content information
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import logging

from app.db.postgres import get_db, get_view_content_popularity

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/content")
async def get_content(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    category: Optional[str] = Query(None, description="Filter by category"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    db: Session = Depends(get_db)
):
    """
    Get all content items with optional filtering.
    
    Args:
        limit: Maximum number of results
        category: Filter by category
        content_type: Filter by content type
    
    Returns:
        List of content items
    """
    try:
        query = """
            SELECT 
                content_id,
                content_type,
                size_kb,
                category,
                created_at,
                updated_at
            FROM content
            WHERE 1=1
        """
        params = {}
        
        if category:
            query += " AND category = :category"
            params["category"] = category
        if content_type:
            query += " AND content_type = :content_type"
            params["content_type"] = content_type
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        result = db.execute(text(query), params)
        columns = result.keys()
        rows = result.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        
        return {
            "status": "success",
            "count": len(data),
            "limit": limit,
            "filters": {
                "category": category,
                "content_type": content_type
            },
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching content: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching content: {str(e)}")


@router.get("/content/{content_id}")
async def get_content_item(
    content_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specific content item by ID.
    Used by edge simulator to fetch content from origin.
    
    Args:
        content_id: Content identifier
    
    Returns:
        Content item details
    """
    try:
        result = db.execute(
            text("""
                SELECT 
                    content_id,
                    content_type,
                    size_kb,
                    category,
                    created_at,
                    updated_at
                FROM content
                WHERE content_id = :content_id
            """),
            {"content_id": content_id}
        )
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Content {content_id} not found")
        
        columns = result.keys()
        data = dict(zip(columns, row))
        
        # Return in format expected by edge simulator
        return {
            "status": "success",
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching content {content_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching content: {str(e)}")


@router.get("/content/popular")
async def get_popular_content(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get popular content from v_content_popularity view.
    
    Args:
        limit: Maximum number of results
    
    Returns:
        List of popular content items with popularity metrics
    """
    try:
        data = get_view_content_popularity(limit=limit, db=db)
        return {
            "status": "success",
            "count": len(data),
            "limit": limit,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching popular content: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching popular content: {str(e)}")
