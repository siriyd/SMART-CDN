"""
AI Engine Main Application
Provides caching intelligence through predictions and policy decisions
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

from ai.schemas import HealthResponse, DecisionRequest, AIDecisionResponse
from ai.predictor import PopularityPredictor
from ai.policy import CachingPolicy
from ai.utils import validate_request_logs, validate_content_metadata, validate_edge_constraints

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart CDN AI Engine",
    description="AI-driven caching prediction and policy engine",
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

# Initialize components
predictor = PopularityPredictor(alpha=0.3, beta=0.2)
policy = CachingPolicy(
    prefetch_threshold=2,  # Lowered for better sensitivity
    eviction_threshold=0,
    min_ttl=60,
    max_ttl=86400
)


@app.get("/")
async def root():
    return {
        "message": "Smart CDN AI Engine",
        "status": "running",
        "mode": "local"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        service="ai-engine",
        version="1.0.0"
    )


@app.post("/decide", response_model=AIDecisionResponse)
async def decide(request: DecisionRequest) -> AIDecisionResponse:
    """
    Main decision endpoint.
    Takes request logs and constraints, returns caching decisions.
    
    Args:
        request: Decision request with logs, metadata, and constraints
    
    Returns:
        AI decision response with predictions and cache decisions
    """
    import traceback
    import sys
    
    try:
        # Log request payload sizes (not raw data for privacy)
        logger.info(
            f"/decide called: "
            f"{len(request.request_logs)} request logs, "
            f"{len(request.content_metadata)} content items, "
            f"{len(request.edge_constraints)} edge constraints, "
            f"time_window={request.time_window_minutes}min"
        )
        
        # Validate inputs
        try:
            validated_logs = validate_request_logs(request.request_logs)
            validated_metadata = validate_content_metadata(request.content_metadata)
            validated_constraints = validate_edge_constraints(request.edge_constraints)
        except Exception as e:
            logger.error(
                f"Validation error in /decide (file: {__file__}, line: {sys._getframe().f_lineno}): {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=400,
                detail=f"Input validation failed: {str(e)}"
            )
        
        if not validated_logs:
            logger.warning("No valid request logs provided")
            # Return empty decisions
            return AIDecisionResponse(
                popularity_forecast=[],
                prefetch_plan=[],
                eviction_plan=[],
                ttl_updates=[],
                model_mode="local"
            )
        
        # Generate popularity forecasts
        try:
            forecasts = predictor.predict_with_metadata(
                request_logs=validated_logs,
                content_metadata=validated_metadata,
                time_window_minutes=request.time_window_minutes
            )
        except Exception as e:
            logger.error(
                f"Prediction error in /decide (file: predictor.py): {e}",
                exc_info=True
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating predictions: {str(e)}"
            )
        
        # Generate caching decisions with fallback mechanism
        # Fallback ensures at least one decision when we have request data
        try:
            prefetch_plan = policy.make_prefetch_plan_with_fallback(
                popularity_forecast=forecasts,
                edge_constraints=validated_constraints,
                content_metadata=validated_metadata,
                request_logs=validated_logs
            )
        except Exception as e:
            logger.error(
                f"Prefetch plan error in /decide (file: policy.py): {e}",
                exc_info=True
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating prefetch plan: {str(e)}"
            )
        
        try:
            eviction_plan = policy.make_eviction_plan(
                popularity_forecast=forecasts,
                edge_constraints=validated_constraints,
                cache_state=None  # Could be provided in request if available
            )
        except Exception as e:
            logger.error(
                f"Eviction plan error in /decide (file: policy.py): {e}",
                exc_info=True
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't fail completely - continue with empty eviction plan
            eviction_plan = []
        
        try:
            ttl_updates = policy.make_ttl_updates(
                popularity_forecast=forecasts,
                cache_state=None  # Could be provided in request if available
            )
        except Exception as e:
            logger.error(
                f"TTL update error in /decide (file: policy.py): {e}",
                exc_info=True
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't fail completely - continue with empty TTL updates
            ttl_updates = []
        
        # Convert forecasts to response format
        try:
            popularity_forecast = [
                {
                    "content_id": f["content_id"],
                    "predicted_requests_next_window": f["predicted_requests_next_window"],
                    "confidence": f["confidence"]
                }
                for f in forecasts
            ]
        except Exception as e:
            logger.error(
                f"Forecast conversion error in /decide (file: {__file__}): {e}",
                exc_info=True
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Error formatting forecasts: {str(e)}"
            )
        
        logger.info(
            f"Generated decisions: {len(prefetch_plan)} prefetch, "
            f"{len(eviction_plan)} evict, {len(ttl_updates)} TTL updates"
        )
        
        try:
            return AIDecisionResponse(
                popularity_forecast=popularity_forecast,
                prefetch_plan=prefetch_plan,
                eviction_plan=eviction_plan,
                ttl_updates=ttl_updates,
                model_mode="local"
            )
        except Exception as e:
            logger.error(
                f"Response creation error in /decide (file: {__file__}): {e}",
                exc_info=True
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Error creating response: {str(e)}"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions (already properly formatted)
        raise
    except Exception as e:
        # Catch-all for any unexpected errors
        logger.error(
            f"Unexpected error in /decide (file: {__file__}, line: {sys._getframe().f_lineno}): {e}",
            exc_info=True
        )
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"Exception type: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error generating decisions: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
