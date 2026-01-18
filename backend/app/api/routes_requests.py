"""
Request Logging API Routes
Endpoints for logging CDN requests to database
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from app.db.postgres import get_db
from app.services.experiment_service import get_active_experiment

logger = logging.getLogger(__name__)

router = APIRouter()


class RequestLog(BaseModel):
    content_id: str
    edge_id: str
    is_cache_hit: bool
    response_time_ms: int
    request_timestamp: Optional[str] = None
    user_ip: Optional[str] = None
    user_agent: Optional[str] = None
    experiment_id: Optional[int] = None


@router.post("/requests/log")
async def log_request(
    request: RequestLog,
    db: Session = Depends(get_db)
):
    """
    Log a CDN request to the database.
    Called by edge simulators to record request metrics.
    Automatically assigns experiment_id if not provided.
    """
    try:
        # Auto-assign experiment_id if not provided
        if request.experiment_id is None:
            active_experiment = get_active_experiment(db)
            if active_experiment:
                request.experiment_id = active_experiment.experiment_id
        
        # Parse timestamp if provided, otherwise use current time
        if request.request_timestamp:
            try:
                timestamp = datetime.fromisoformat(request.request_timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()
        
        # Insert request into database
        result = db.execute(
            text("""
                INSERT INTO requests (
                    content_id, edge_id, is_cache_hit, response_time_ms,
                    request_timestamp, user_ip, user_agent, experiment_id
                ) VALUES (
                    :content_id, :edge_id, :is_cache_hit, :response_time_ms,
                    :request_timestamp, :user_ip, :user_agent, :experiment_id
                )
                RETURNING request_id
            """),
            {
                "content_id": request.content_id,
                "edge_id": request.edge_id,
                "is_cache_hit": request.is_cache_hit,
                "response_time_ms": request.response_time_ms,
                "request_timestamp": timestamp,
                "user_ip": request.user_ip,
                "user_agent": request.user_agent,
                "experiment_id": request.experiment_id
            }
        )
        
        db.commit()
        request_id = result.fetchone()[0]
        
        logger.debug(f"Logged request {request_id}: {request.content_id} at {request.edge_id}")
        
        return {
            "status": "success",
            "request_id": request_id,
            "message": "Request logged successfully"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging request: {e}")
        raise HTTPException(status_code=500, detail=f"Error logging request: {str(e)}")


@router.get("/requests")
async def get_requests(
    limit: int = 100,
    edge_id: Optional[str] = None,
    content_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get recent requests with optional filtering.
    """
    try:
        query = """
            SELECT 
                request_id, content_id, edge_id, is_cache_hit,
                response_time_ms, request_timestamp, user_ip, user_agent
            FROM requests
            WHERE 1=1
        """
        params = {"limit": limit}
        
        if edge_id:
            query += " AND edge_id = :edge_id"
            params["edge_id"] = edge_id
        
        if content_id:
            query += " AND content_id = :content_id"
            params["content_id"] = content_id
        
        query += " ORDER BY request_timestamp DESC LIMIT :limit"
        
        result = db.execute(text(query), params)
        columns = result.keys()
        rows = result.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching requests: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching requests: {str(e)}")

