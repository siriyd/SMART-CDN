"""
Experiments API Routes
Endpoints for managing A/B experiments (AI ON vs AI OFF)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from app.db.postgres import get_db
from app.services.experiment_service import (
    get_active_experiment,
    is_ai_enabled,
    toggle_ai_mode,
    get_experiment_results,
    compare_experiments
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class ExperimentToggleRequest(BaseModel):
    ai_enabled: bool


class ExperimentCreateRequest(BaseModel):
    experiment_name: str
    ai_enabled: bool
    description: Optional[str] = None


@router.get("/experiments/status")
async def get_experiment_status(
    db: Session = Depends(get_db)
):
    """
    Get current experiment status (AI enabled or not).
    
    Returns:
        Current experiment status
    """
    try:
        experiment = get_active_experiment(db)
        ai_enabled = is_ai_enabled(db)
        
        return {
            "ai_enabled": ai_enabled,
            "experiment": {
                "experiment_id": experiment.experiment_id if experiment else None,
                "experiment_name": experiment.experiment_name if experiment else "No active experiment",
                "is_active": experiment.is_active if experiment else False,
                "start_time": experiment.start_time.isoformat() if experiment and experiment.start_time else None
            }
        }
    except Exception as e:
        logger.error(f"Error getting experiment status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting experiment status: {str(e)}")


@router.post("/experiments/toggle")
async def toggle_experiment(
    request: ExperimentToggleRequest,
    db: Session = Depends(get_db)
):
    """
    Toggle AI mode (ON/OFF) by creating a new experiment.
    Public endpoint for demo/academic purposes.
    
    Args:
        request: Toggle request with ai_enabled flag
        db: Database session
    
    Returns:
        Created experiment
    """
    try:
        experiment = toggle_ai_mode(db, request.ai_enabled)
        return {
            "status": "success",
            "message": f"AI mode {'enabled' if request.ai_enabled else 'disabled'}",
            "experiment": {
                "experiment_id": experiment.experiment_id,
                "experiment_name": experiment.experiment_name,
                "ai_enabled": experiment.ai_enabled,
                "start_time": experiment.start_time.isoformat() if experiment.start_time else None
            }
        }
    except Exception as e:
        logger.error(f"Error toggling experiment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error toggling experiment: {str(e)}")


@router.post("/experiments/create")
async def create_experiment(
    request: ExperimentCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new experiment.
    Public endpoint for demo/academic purposes.
    
    Args:
        request: Experiment creation request
        db: Database session
    
    Returns:
        Created experiment
    """
    try:
        from app.services.experiment_service import create_experiment
        experiment = create_experiment(
            db,
            request.experiment_name,
            request.ai_enabled,
            request.description
        )
        return {
            "status": "success",
            "experiment": {
                "experiment_id": experiment.experiment_id,
                "experiment_name": experiment.experiment_name,
                "ai_enabled": experiment.ai_enabled,
                "start_time": experiment.start_time.isoformat() if experiment.start_time else None
            }
        }
    except Exception as e:
        logger.error(f"Error creating experiment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating experiment: {str(e)}")


@router.get("/experiments/results")
async def get_experiment_results_endpoint(
    experiment_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get results for an experiment.
    
    Args:
        experiment_id: Optional experiment ID (uses active experiment if not provided)
        db: Database session
    
    Returns:
        Experiment results with metrics
    """
    try:
        results = get_experiment_results(db, experiment_id)
        if "error" in results:
            raise HTTPException(status_code=404, detail=results["error"])
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting experiment results: {str(e)}")


@router.get("/experiments/compare")
async def compare_experiments_endpoint(
    ai_experiment_id: int = Query(..., description="Experiment ID with AI enabled"),
    baseline_experiment_id: int = Query(..., description="Experiment ID with AI disabled"),
    db: Session = Depends(get_db)
):
    """
    Compare two experiments (AI vs Baseline).
    
    Args:
        ai_experiment_id: Experiment ID with AI enabled
        baseline_experiment_id: Experiment ID with AI disabled
        db: Database session
    
    Returns:
        Comparison results with improvement percentages
    """
    try:
        comparison = compare_experiments(db, ai_experiment_id, baseline_experiment_id)
        if "error" in comparison:
            raise HTTPException(status_code=400, detail=comparison["error"])
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing experiments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error comparing experiments: {str(e)}")


@router.get("/experiments/list")
async def list_experiments(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List all experiments.
    
    Args:
        limit: Maximum number of experiments to return
        db: Database session
    
    Returns:
        List of experiments
    """
    try:
        from app.db.models import Experiment
        experiments = db.query(Experiment).order_by(
            Experiment.start_time.desc()
        ).limit(limit).all()
        
        return {
            "count": len(experiments),
            "experiments": [
                {
                    "experiment_id": exp.experiment_id,
                    "experiment_name": exp.experiment_name,
                    "ai_enabled": exp.ai_enabled,
                    "start_time": exp.start_time.isoformat() if exp.start_time else None,
                    "end_time": exp.end_time.isoformat() if exp.end_time else None,
                    "is_active": exp.is_active,
                    "description": exp.description
                }
                for exp in experiments
            ]
        }
    except Exception as e:
        logger.error(f"Error listing experiments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing experiments: {str(e)}")

