"""
Experiment Service
Manages A/B testing between AI-enabled and baseline caching modes
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

from app.db.models import Experiment

logger = logging.getLogger(__name__)


def get_active_experiment(db: Session) -> Optional[Experiment]:
    """
    Get the currently active experiment.
    
    Returns:
        Active experiment or None if no experiment is active
    """
    try:
        experiment = db.query(Experiment).filter(
            Experiment.is_active == True
        ).first()
        return experiment
    except Exception as e:
        logger.error(f"Error getting active experiment: {e}", exc_info=True)
        return None


def is_ai_enabled(db: Session) -> bool:
    """
    Check if AI is currently enabled in the active experiment.
    
    Returns:
        True if AI is enabled, False otherwise (defaults to False if no experiment)
    """
    experiment = get_active_experiment(db)
    if experiment:
        return experiment.ai_enabled
    # Default to AI enabled if no experiment exists
    return True


def create_experiment(
    db: Session,
    experiment_name: str,
    ai_enabled: bool,
    description: Optional[str] = None
) -> Experiment:
    """
    Create a new experiment and deactivate any existing active experiments.
    
    Args:
        db: Database session
        experiment_name: Name of the experiment
        ai_enabled: Whether AI is enabled for this experiment
        description: Optional description
    
    Returns:
        Created experiment
    """
    try:
        # Deactivate all existing experiments
        db.execute(text("""
            UPDATE experiments 
            SET is_active = false, end_time = CURRENT_TIMESTAMP
            WHERE is_active = true
        """))
        
        # Create new experiment
        experiment = Experiment(
            experiment_name=experiment_name,
            ai_enabled=ai_enabled,
            description=description,
            is_active=True,
            start_time=datetime.now(timezone.utc)
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        
        logger.info(f"Created experiment: {experiment_name} (AI enabled: {ai_enabled})")
        return experiment
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating experiment: {e}", exc_info=True)
        raise


def toggle_ai_mode(db: Session, ai_enabled: bool) -> Experiment:
    """
    Toggle AI mode by creating a new experiment.
    
    Args:
        db: Database session
        ai_enabled: Whether to enable AI
    
    Returns:
        Created experiment
    """
    mode_name = "AI-Enabled" if ai_enabled else "Baseline"
    description = f"AI-driven caching {'enabled' if ai_enabled else 'disabled'} (baseline LRU/LFU)"
    return create_experiment(db, f"{mode_name} Mode", ai_enabled, description)


def get_experiment_results(
    db: Session,
    experiment_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get metrics comparison for an experiment.
    
    Args:
        db: Database session
        experiment_id: Optional experiment ID (uses active experiment if not provided)
    
    Returns:
        Dictionary with experiment results and metrics
    """
    try:
        if experiment_id:
            experiment = db.query(Experiment).filter(
                Experiment.experiment_id == experiment_id
            ).first()
        else:
            experiment = get_active_experiment(db)
        
        if not experiment:
            return {
                "error": "No experiment found",
                "experiment": None
            }
        
        # Get metrics for this experiment
        # Calculate from requests table filtered by experiment_id
        metrics_query = text("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN is_cache_hit = true THEN 1 ELSE 0 END) as cache_hits,
                SUM(CASE WHEN is_cache_hit = false THEN 1 ELSE 0 END) as cache_misses,
                AVG(response_time_ms) as avg_response_time_ms,
                AVG(CASE WHEN is_cache_hit = true THEN response_time_ms END) as avg_hit_latency_ms,
                AVG(CASE WHEN is_cache_hit = false THEN response_time_ms END) as avg_miss_latency_ms,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as p50_latency_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_latency_ms,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_latency_ms
            FROM requests
            WHERE experiment_id = :experiment_id
        """)
        
        result = db.execute(metrics_query, {"experiment_id": experiment.experiment_id})
        row = result.fetchone()
        
        if not row or row[0] is None:
            return {
                "experiment": {
                    "experiment_id": experiment.experiment_id,
                    "experiment_name": experiment.experiment_name,
                    "ai_enabled": experiment.ai_enabled,
                    "start_time": experiment.start_time.isoformat() if experiment.start_time else None,
                    "end_time": experiment.end_time.isoformat() if experiment.end_time else None,
                },
                "metrics": {
                    "total_requests": 0,
                    "cache_hit_ratio": 0.0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "avg_response_time_ms": 0.0,
                    "avg_hit_latency_ms": 0.0,
                    "avg_miss_latency_ms": 0.0,
                    "p50_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                    "p99_latency_ms": 0.0
                }
            }
        
        total_requests = row[0] or 0
        cache_hits = row[1] or 0
        cache_misses = row[2] or 0
        cache_hit_ratio = (cache_hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "experiment": {
                "experiment_id": experiment.experiment_id,
                "experiment_name": experiment.experiment_name,
                "ai_enabled": experiment.ai_enabled,
                "start_time": experiment.start_time.isoformat() if experiment.start_time else None,
                "end_time": experiment.end_time.isoformat() if experiment.end_time else None,
                "description": experiment.description,
                "is_active": experiment.is_active
            },
            "metrics": {
                "total_requests": total_requests,
                "cache_hit_ratio": round(cache_hit_ratio, 2),
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "avg_response_time_ms": round(float(row[3] or 0), 2),
                "avg_hit_latency_ms": round(float(row[4] or 0), 2),
                "avg_miss_latency_ms": round(float(row[5] or 0), 2),
                "p50_latency_ms": round(float(row[6] or 0), 2),
                "p95_latency_ms": round(float(row[7] or 0), 2),
                "p99_latency_ms": round(float(row[8] or 0), 2)
            }
        }
    except Exception as e:
        logger.error(f"Error getting experiment results: {e}", exc_info=True)
        return {
            "error": str(e),
            "experiment": None
        }


def compare_experiments(
    db: Session,
    ai_experiment_id: int,
    baseline_experiment_id: int
) -> Dict[str, Any]:
    """
    Compare two experiments (AI vs Baseline).
    
    Args:
        db: Database session
        ai_experiment_id: Experiment ID with AI enabled
        baseline_experiment_id: Experiment ID with AI disabled
    
    Returns:
        Comparison results with improvement percentages
    """
    try:
        ai_results = get_experiment_results(db, ai_experiment_id)
        baseline_results = get_experiment_results(db, baseline_experiment_id)
        
        if "error" in ai_results or "error" in baseline_results:
            return {
                "error": "Could not retrieve experiment results",
                "ai_experiment": ai_results.get("experiment"),
                "baseline_experiment": baseline_results.get("experiment")
            }
        
        ai_metrics = ai_results["metrics"]
        baseline_metrics = baseline_results["metrics"]
        
        # Calculate improvements
        hit_ratio_improvement = 0.0
        if baseline_metrics["cache_hit_ratio"] > 0:
            hit_ratio_improvement = (
                (ai_metrics["cache_hit_ratio"] - baseline_metrics["cache_hit_ratio"]) /
                baseline_metrics["cache_hit_ratio"] * 100
            )
        
        latency_improvement = 0.0
        if baseline_metrics["avg_response_time_ms"] > 0:
            latency_improvement = (
                (baseline_metrics["avg_response_time_ms"] - ai_metrics["avg_response_time_ms"]) /
                baseline_metrics["avg_response_time_ms"] * 100
            )
        
        return {
            "ai_experiment": ai_results["experiment"],
            "baseline_experiment": baseline_results["experiment"],
            "ai_metrics": ai_metrics,
            "baseline_metrics": baseline_metrics,
            "improvements": {
                "cache_hit_ratio_improvement_pct": round(hit_ratio_improvement, 2),
                "latency_improvement_pct": round(latency_improvement, 2),
                "cache_hits_improvement": ai_metrics["cache_hits"] - baseline_metrics["cache_hits"],
                "latency_reduction_ms": round(
                    baseline_metrics["avg_response_time_ms"] - ai_metrics["avg_response_time_ms"],
                    2
                )
            }
        }
    except Exception as e:
        logger.error(f"Error comparing experiments: {e}", exc_info=True)
        return {
            "error": str(e)
        }
