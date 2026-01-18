"""
SQLAlchemy Models
ORM models matching the database schema
"""
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.postgres import Base


class EdgeNode(Base):
    """Edge node model"""
    __tablename__ = "edge_nodes"
    
    edge_id = Column(String(50), primary_key=True)
    region = Column(String(50), nullable=False)
    cache_capacity_mb = Column(Integer, nullable=False, default=100)
    current_usage_mb = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    requests = relationship("Request", back_populates="edge")
    cache_entries = relationship("CacheState", back_populates="edge")
    ai_decisions = relationship("AIDecision", back_populates="edge")


class Content(Base):
    """Content metadata model"""
    __tablename__ = "content"
    
    content_id = Column(String(100), primary_key=True)
    content_type = Column(String(50), nullable=False)
    size_kb = Column(Integer, nullable=False)
    category = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    requests = relationship("Request", back_populates="content")
    cache_entries = relationship("CacheState", back_populates="content")
    ai_decisions = relationship("AIDecision", back_populates="content")


class Request(Base):
    """Request log model"""
    __tablename__ = "requests"
    
    request_id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String(100), ForeignKey("content.content_id", ondelete="CASCADE"), nullable=False)
    edge_id = Column(String(50), ForeignKey("edge_nodes.edge_id", ondelete="CASCADE"), nullable=False)
    is_cache_hit = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    request_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_ip = Column(String(45))
    user_agent = Column(Text)
    experiment_id = Column(Integer, ForeignKey("experiments.experiment_id", ondelete="SET NULL"))
    
    # Relationships
    content = relationship("Content", back_populates="requests")
    edge = relationship("EdgeNode", back_populates="requests")
    experiment = relationship("Experiment", back_populates="requests")
    
    # Indexes are defined in schema.sql, but can also be added here:
    __table_args__ = (
        Index("idx_requests_content_time", "content_id", "request_timestamp"),
        Index("idx_requests_edge_time", "edge_id", "request_timestamp"),
    )


class AIDecision(Base):
    """AI decision model"""
    __tablename__ = "ai_decisions"
    
    decision_id = Column(Integer, primary_key=True, autoincrement=True)
    decision_type = Column(String(20), nullable=False)  # 'prefetch', 'evict', 'ttl_update'
    content_id = Column(String(100), ForeignKey("content.content_id", ondelete="CASCADE"), nullable=False)
    edge_id = Column(String(50), ForeignKey("edge_nodes.edge_id", ondelete="CASCADE"))
    ttl_seconds = Column(Integer)
    priority = Column(Integer, nullable=False, default=0)
    reason = Column(Text)
    predicted_popularity = Column(Integer)
    decision_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    applied_at = Column(DateTime(timezone=True))
    experiment_id = Column(Integer, ForeignKey("experiments.experiment_id", ondelete="SET NULL"))
    
    # Relationships
    content = relationship("Content", back_populates="ai_decisions")
    edge = relationship("EdgeNode", back_populates="ai_decisions")
    experiment = relationship("Experiment", back_populates="ai_decisions")


class Experiment(Base):
    """Experiment model for A/B testing"""
    __tablename__ = "experiments"
    
    experiment_id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_name = Column(String(100), nullable=False)
    ai_enabled = Column(Boolean, nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True))
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    requests = relationship("Request", back_populates="experiment")
    ai_decisions = relationship("AIDecision", back_populates="experiment")


class Metric(Base):
    """Metrics aggregation model"""
    __tablename__ = "metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    metric_type = Column(String(50), nullable=False)
    edge_id = Column(String(50), ForeignKey("edge_nodes.edge_id", ondelete="CASCADE"))
    content_id = Column(String(100), ForeignKey("content.content_id", ondelete="CASCADE"))
    metric_value = Column(Numeric(10, 4), nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.experiment_id", ondelete="SET NULL"))
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CacheState(Base):
    """Cache state model"""
    __tablename__ = "cache_state"
    
    cache_entry_id = Column(Integer, primary_key=True, autoincrement=True)
    edge_id = Column(String(50), ForeignKey("edge_nodes.edge_id", ondelete="CASCADE"), nullable=False)
    content_id = Column(String(100), ForeignKey("content.content_id", ondelete="CASCADE"), nullable=False)
    cached_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ttl_seconds = Column(Integer, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    access_count = Column(Integer, nullable=False, default=0)
    last_accessed_at = Column(DateTime(timezone=True))
    
    # Relationships
    edge = relationship("EdgeNode", back_populates="cache_entries")
    content = relationship("Content", back_populates="cache_entries")
    
    __table_args__ = (
        Index("idx_cache_state_edge_content", "edge_id", "content_id", unique=True),
    )
