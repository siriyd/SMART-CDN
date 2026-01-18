"""
AI Decision API Routes
Endpoints for triggering AI decisions and applying them
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.db.postgres import get_db
from app.services.ai_client import AIClient
from app.services.cdn_logic import CDNLogicService
from app.services.experiment_service import is_ai_enabled, get_active_experiment

logger = logging.getLogger(__name__)

router = APIRouter()

# Global clients (initialized on first use)
ai_client: Optional[AIClient] = None
cdn_logic: Optional[CDNLogicService] = None


def get_ai_client() -> AIClient:
    """Get or create AI client"""
    global ai_client
    if ai_client is None:
        ai_client = AIClient()
    return ai_client


def get_cdn_logic() -> CDNLogicService:
    """Get or create CDN logic service"""
    global cdn_logic
    if cdn_logic is None:
        cdn_logic = CDNLogicService()
    return cdn_logic


@router.post("/ai/decide")
async def trigger_ai_decisions(
    time_window_minutes: int = Query(60, ge=1, le=1440),
    apply_decisions: bool = Query(True, description="Apply decisions to caches immediately"),
    experiment_id: Optional[int] = Query(None, description="Experiment ID"),
    db: Session = Depends(get_db)
):
    """
    Trigger AI decision generation and optionally apply to caches.
    Only works if AI is enabled in the active experiment.
    
    Args:
        time_window_minutes: Prediction time window
        apply_decisions: Whether to apply decisions immediately
        experiment_id: Optional experiment ID
    
    Returns:
        AI decisions and application results
    """
    try:
        # Get recent request logs
        window_start = datetime.utcnow() - timedelta(minutes=time_window_minutes * 2)
        
        result = db.execute(
            text("""
                SELECT 
                    content_id, edge_id, is_cache_hit, response_time_ms,
                    request_timestamp, user_ip, user_agent
                FROM requests
                WHERE request_timestamp >= :window_start
                ORDER BY request_timestamp DESC
                LIMIT 1000
            """),
            {"window_start": window_start}
        )
        
        columns = result.keys()
        rows = result.fetchall()
        request_logs = [dict(zip(columns, row)) for row in rows]
        
        # Get content metadata
        content_ids = list(set([log["content_id"] for log in request_logs]))
        if not content_ids:
            raise HTTPException(status_code=400, detail="No request logs found")
        
        placeholders = ",".join([f":id{i}" for i in range(len(content_ids))])
        params = {f"id{i}": content_ids[i] for i in range(len(content_ids))}
        
        result = db.execute(
            text(f"""
                SELECT content_id, content_type, size_kb, category
                FROM content
                WHERE content_id IN ({placeholders})
            """),
            params
        )
        
        columns = result.keys()
        rows = result.fetchall()
        content_metadata = [dict(zip(columns, row)) for row in rows]
        
        # Get edge constraints
        result = db.execute(
            text("""
                SELECT 
                    edge_id, region, cache_capacity_mb, current_usage_mb, is_active
                FROM edge_nodes
                WHERE is_active = TRUE
            """)
        )
        
        columns = result.keys()
        rows = result.fetchall()
        edge_constraints = [dict(zip(columns, row)) for row in rows]
        
        # Get AI decisions
        ai_client = get_ai_client()
        
        logger.info(
            f"Requesting AI decisions: {len(request_logs)} logs, "
            f"{len(content_metadata)} content items, {len(edge_constraints)} edges"
        )
        
        decisions = await ai_client.get_decisions(
            request_logs=request_logs,
            content_metadata=content_metadata,
            edge_constraints=edge_constraints,
            time_window_minutes=time_window_minutes
        )
        
        if decisions is None:
            # None means an error occurred (already logged in ai_client)
            logger.error("AI client returned None - check logs above for details")
            raise HTTPException(
                status_code=500, 
                detail="Failed to get AI decisions. Check backend logs for details."
            )
        
        # Validate decisions structure
        if not isinstance(decisions, dict):
            logger.error(f"AI decisions is not a dict: {type(decisions)}")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid AI decision response format: expected dict, got {type(decisions).__name__}"
            )
        
        # Empty but valid responses are acceptable (no predictions when no data)
        logger.info(f"AI decisions received successfully (may be empty if no data)")
        
        # Check if there are any actionable decisions
        prefetch_plan = decisions.get("prefetch_plan", [])
        eviction_plan = decisions.get("eviction_plan", [])
        ttl_updates = decisions.get("ttl_updates", [])
        
        has_actionable_decisions = (
            len(prefetch_plan) > 0 or
            len(eviction_plan) > 0 or
            len(ttl_updates) > 0
        )
        
        # Store decisions in database only if there are actionable decisions
        # (ai_decisions.content_id is NOT NULL, so we can't insert batch rows with NULLs)
        decision_id = None
        if has_actionable_decisions:
            try:
                # Store individual decisions (not batch row)
                # For each actionable decision, insert a row with proper content_id
                stored_count = 0
                for item in prefetch_plan:
                    content_id = item.get("content_id")
                    target_edges = item.get("target_edges", [])
                    ttl_seconds = item.get("ttl_seconds")
                    priority = item.get("priority", 0)
                    
                    for edge_id in target_edges:
                        result = db.execute(
                            text("""
                                INSERT INTO ai_decisions (
                                    decision_type, content_id, edge_id, ttl_seconds,
                                    priority, reason, predicted_popularity, experiment_id
                                ) VALUES (
                                    'prefetch', :content_id, :edge_id, :ttl_seconds,
                                    :priority, 'AI prefetch decision', NULL, :experiment_id
                                )
                                RETURNING decision_id
                            """),
                            {
                                "content_id": content_id,
                                "edge_id": edge_id,
                                "ttl_seconds": ttl_seconds,
                                "priority": priority,
                                "experiment_id": experiment_id
                            }
                        )
                        stored_count += 1
                        if decision_id is None:  # Keep first decision_id for response
                            decision_id = result.fetchone()[0]
                
                for item in eviction_plan:
                    content_id = item.get("content_id")
                    edge_id = item.get("edge_id")
                    reason = item.get("reason", "AI eviction decision")
                    priority = item.get("priority", 0)
                    
                    result = db.execute(
                        text("""
                            INSERT INTO ai_decisions (
                                decision_type, content_id, edge_id, ttl_seconds,
                                priority, reason, predicted_popularity, experiment_id
                            ) VALUES (
                                'evict', :content_id, :edge_id, NULL,
                                :priority, :reason, NULL, :experiment_id
                            )
                            RETURNING decision_id
                        """),
                        {
                            "content_id": content_id,
                            "edge_id": edge_id,
                            "priority": priority,
                            "reason": reason,
                            "experiment_id": experiment_id
                        }
                    )
                    stored_count += 1
                    if decision_id is None:
                        decision_id = result.fetchone()[0]
                
                for item in ttl_updates:
                    content_id = item.get("content_id")
                    edge_id = item.get("edge_id")
                    ttl_seconds = item.get("new_ttl_seconds")
                    
                    result = db.execute(
                        text("""
                            INSERT INTO ai_decisions (
                                decision_type, content_id, edge_id, ttl_seconds,
                                priority, reason, predicted_popularity, experiment_id
                            ) VALUES (
                                'ttl_update', :content_id, :edge_id, :ttl_seconds,
                                0, 'AI TTL update', NULL, :experiment_id
                            )
                            RETURNING decision_id
                        """),
                        {
                            "content_id": content_id,
                            "edge_id": edge_id,
                            "ttl_seconds": ttl_seconds,
                            "experiment_id": experiment_id
                        }
                    )
                    stored_count += 1
                    if decision_id is None:
                        decision_id = result.fetchone()[0]
                
                db.commit()
                logger.info(f"Stored {stored_count} AI decision(s) in database")
            except Exception as e:
                db.rollback()
                logger.error(f"Error storing decisions: {e}")
        else:
            logger.info("No actionable AI decisions generated; skipping database insert")
        
        # Apply decisions if requested
        application_results = None
        if apply_decisions:
            cdn_logic = get_cdn_logic()
            application_results = await cdn_logic.apply_decisions(decisions, experiment_id)
        
        return {
            "status": "success",
            "decisions": decisions,
            "application_results": application_results,
            "decision_id": decision_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering AI decisions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/ai/decisions")
async def get_ai_decisions(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recent AI decisions from database.
    """
    try:
        result = db.execute(
            text("""
                SELECT 
                    decision_id, decision_type, content_id, edge_id,
                    ttl_seconds, priority, reason, predicted_popularity,
                    decision_timestamp, applied_at, experiment_id
                FROM ai_decisions
                ORDER BY decision_timestamp DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        columns = result.keys()
        rows = result.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error fetching AI decisions: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
