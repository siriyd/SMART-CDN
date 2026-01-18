from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.core.config import settings
from app.db.postgres import get_db, check_db_connection, get_view_cache_hit_ratio, get_view_latency_by_edge, get_view_content_popularity

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart CDN Backend API",
    description="Backend API for Smart CDN with AI-Driven Caching",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Check database connection on startup"""
    logger.info("Starting Smart CDN Backend API...")
    if check_db_connection():
        logger.info("Database connection successful")
    else:
        logger.warning("Database connection check failed - will retry on first request")


@app.get("/")
async def root():
    return {
        "message": "Smart CDN Backend API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """
    Health check endpoint with database connectivity check.
    """
    db_status = "connected"
    try:
        # Test database query
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "backend",
        "version": "1.0.0",
        "database": db_status
    }


@app.get("/api/v1/db/status")
async def db_status(db: Session = Depends(get_db)):
    """
    Get detailed database status and connection information.
    """
    try:
        # Test connection
        result = db.execute(text("SELECT version()"))
        pg_version = result.fetchone()[0]
        
        # Get table count
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        table_count = result.fetchone()[0]
        
        # Get view count
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.views 
            WHERE table_schema = 'public'
        """))
        view_count = result.fetchone()[0]
        
        return {
            "status": "connected",
            "postgres_version": pg_version.split(",")[0],  # Get first part
            "database": settings.POSTGRES_DB,
            "tables": table_count,
            "views": view_count
        }
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


# Include API routes
from app.api import routes_metrics, routes_edges, routes_content, routes_requests, routes_ai, routes_auth, routes_experiments

app.include_router(routes_metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(routes_edges.router, prefix="/api/v1", tags=["edges"])
app.include_router(routes_content.router, prefix="/api/v1", tags=["content"])
app.include_router(routes_requests.router, prefix="/api/v1", tags=["requests"])
app.include_router(routes_ai.router, prefix="/api/v1", tags=["ai"])
app.include_router(routes_auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(routes_experiments.router, prefix="/api/v1", tags=["experiments"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


