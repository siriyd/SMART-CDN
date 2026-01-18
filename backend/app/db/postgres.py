"""
PostgreSQL Database Adapter
SQLAlchemy setup for database connections and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions (for use outside FastAPI routes).
    Usage:
        with get_db_context() as db:
            items = db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database: create all tables.
    Note: Schema SQL is loaded via docker-entrypoint-initdb.d,
    but this can be used to create tables from SQLAlchemy models.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def execute_view(view_name: str, db: Session = None) -> list:
    """
    Execute a database view and return results.
    
    Args:
        view_name: Name of the view to query
        db: Optional database session (if None, creates new session)
    
    Returns:
        List of dictionaries with view results
    """
    if db is None:
        with get_db_context() as session:
            return execute_view(view_name, session)
    
    try:
        result = db.execute(text(f"SELECT * FROM {view_name}"))
        columns = result.keys()
        rows = result.fetchall()
        
        # Convert to list of dictionaries
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Error executing view {view_name}: {e}")
        raise


def get_view_cache_hit_ratio(db: Session = None) -> list:
    """
    Get cache hit ratio by edge from view v_cache_hit_ratio.
    
    Returns:
        List of dictionaries with cache hit ratio statistics per edge
    """
    return execute_view("v_cache_hit_ratio", db)


def get_view_latency_by_edge(db: Session = None) -> list:
    """
    Get latency metrics by edge from view v_latency_by_edge.
    
    Returns:
        List of dictionaries with latency statistics per edge
    """
    return execute_view("v_latency_by_edge", db)


def get_view_content_popularity(limit: int = 20, db: Session = None) -> list:
    """
    Get content popularity from view v_content_popularity.
    
    Args:
        limit: Maximum number of results to return
        db: Optional database session
    
    Returns:
        List of dictionaries with content popularity metrics
    """
    if db is None:
        with get_db_context() as session:
            return get_view_content_popularity(limit, session)
    
    try:
        result = db.execute(
            text("SELECT * FROM v_content_popularity LIMIT :limit"),
            {"limit": limit}
        )
        columns = result.keys()
        rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Error getting content popularity: {e}")
        raise


# Test connection on module import (optional, can be removed if too aggressive)
if __name__ != "__main__":
    try:
        check_db_connection()
    except Exception:
        # Connection will be checked when backend starts
        pass
