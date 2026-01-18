-- Smart CDN Database Schema
-- Normalized tables for requests, content, edges, metrics, AI decisions, and experiments

-- Edge Nodes Table
-- Stores information about edge cache nodes
CREATE TABLE IF NOT EXISTS edge_nodes (
    edge_id VARCHAR(50) PRIMARY KEY,
    region VARCHAR(50) NOT NULL,
    cache_capacity_mb INTEGER NOT NULL DEFAULT 100,
    current_usage_mb INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Content Metadata Table
-- Stores information about cached content
CREATE TABLE IF NOT EXISTS content (
    content_id VARCHAR(100) PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL, -- e.g., 'video', 'image', 'html', 'json'
    size_kb INTEGER NOT NULL,
    category VARCHAR(50), -- e.g., 'entertainment', 'news', 'sports'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Request Logs Table
-- Stores all CDN requests with hit/miss information
CREATE TABLE IF NOT EXISTS requests (
    request_id SERIAL PRIMARY KEY,
    content_id VARCHAR(100) NOT NULL REFERENCES content(content_id) ON DELETE CASCADE,
    edge_id VARCHAR(50) NOT NULL REFERENCES edge_nodes(edge_id) ON DELETE CASCADE,
    is_cache_hit BOOLEAN NOT NULL,
    response_time_ms INTEGER NOT NULL,
    request_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_ip VARCHAR(45), -- IPv4 or IPv6
    user_agent TEXT,
    experiment_id INTEGER -- Links to experiments table (nullable, FK added later)
);

-- AI Decisions Table
-- Stores AI-generated caching decisions (prefetch, evict, TTL updates)
CREATE TABLE IF NOT EXISTS ai_decisions (
    decision_id SERIAL PRIMARY KEY,
    decision_type VARCHAR(20) NOT NULL, -- 'prefetch', 'evict', 'ttl_update'
    content_id VARCHAR(100) NOT NULL REFERENCES content(content_id) ON DELETE CASCADE,
    edge_id VARCHAR(50) REFERENCES edge_nodes(edge_id) ON DELETE CASCADE,
    ttl_seconds INTEGER, -- For prefetch and TTL updates
    priority INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    predicted_popularity INTEGER, -- Predicted request count
    decision_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP WITH TIME ZONE, -- When decision was applied to cache
    experiment_id INTEGER -- Links to experiments table (FK added later)
);

-- Experiments Table
-- Stores A/B experiment configurations (AI ON vs AI OFF)
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(100) NOT NULL,
    ai_enabled BOOLEAN NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Metrics Aggregation Table
-- Stores pre-computed metrics for faster dashboard queries
CREATE TABLE IF NOT EXISTS metrics (
    metric_id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL, -- 'hit_ratio', 'avg_latency', 'origin_fetches', etc.
    edge_id VARCHAR(50) REFERENCES edge_nodes(edge_id) ON DELETE CASCADE,
    content_id VARCHAR(100) REFERENCES content(content_id) ON DELETE CASCADE,
    metric_value NUMERIC(10, 4) NOT NULL,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    experiment_id INTEGER REFERENCES experiments(experiment_id) ON DELETE SET NULL,
    computed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Cache State Table
-- Tracks current cache state at each edge (what's cached, TTLs)
CREATE TABLE IF NOT EXISTS cache_state (
    cache_entry_id SERIAL PRIMARY KEY,
    edge_id VARCHAR(50) NOT NULL REFERENCES edge_nodes(edge_id) ON DELETE CASCADE,
    content_id VARCHAR(100) NOT NULL REFERENCES content(content_id) ON DELETE CASCADE,
    cached_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ttl_seconds INTEGER NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(edge_id, content_id)
);

-- Add foreign key constraint for requests.experiment_id
ALTER TABLE requests 
ADD CONSTRAINT fk_requests_experiment 
FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE SET NULL;

-- Add foreign key constraint for ai_decisions.experiment_id
ALTER TABLE ai_decisions 
ADD CONSTRAINT fk_ai_decisions_experiment 
FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE SET NULL;

-- Create indexes for requests table
CREATE INDEX IF NOT EXISTS idx_requests_content_id ON requests(content_id);
CREATE INDEX IF NOT EXISTS idx_requests_edge_id ON requests(edge_id);
CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests(request_timestamp);
CREATE INDEX IF NOT EXISTS idx_requests_cache_hit ON requests(is_cache_hit);
CREATE INDEX IF NOT EXISTS idx_requests_content_time ON requests(content_id, request_timestamp);
CREATE INDEX IF NOT EXISTS idx_requests_edge_time ON requests(edge_id, request_timestamp);

-- Create indexes for ai_decisions table
CREATE INDEX IF NOT EXISTS idx_ai_decisions_type ON ai_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_content_id ON ai_decisions(content_id);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_edge_id ON ai_decisions(edge_id);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_timestamp ON ai_decisions(decision_timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_applied ON ai_decisions(applied_at) WHERE applied_at IS NOT NULL;

-- Create indexes for experiments table
CREATE INDEX IF NOT EXISTS idx_experiments_active ON experiments(is_active);
CREATE INDEX IF NOT EXISTS idx_experiments_start_time ON experiments(start_time);

-- Create indexes for metrics table
CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_metrics_window ON metrics(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_metrics_edge_id ON metrics(edge_id);
CREATE INDEX IF NOT EXISTS idx_metrics_content_id ON metrics(content_id);

-- Create indexes for cache_state table
CREATE INDEX IF NOT EXISTS idx_cache_state_edge_id ON cache_state(edge_id);
CREATE INDEX IF NOT EXISTS idx_cache_state_content_id ON cache_state(content_id);
CREATE INDEX IF NOT EXISTS idx_cache_state_expires_at ON cache_state(expires_at);

-- Insert default edge nodes (3 regions as specified)
INSERT INTO edge_nodes (edge_id, region, cache_capacity_mb, is_active) VALUES
    ('edge-us-east', 'us-east', 100, TRUE),
    ('edge-us-west', 'us-west', 100, TRUE),
    ('edge-eu-west', 'eu-west', 100, TRUE)
ON CONFLICT (edge_id) DO NOTHING;

-- Insert default experiment (AI OFF baseline)
-- Note: experiments table doesn't have a unique constraint, so we check if it exists first
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM experiments WHERE experiment_name = 'baseline-no-ai') THEN
        INSERT INTO experiments (experiment_name, ai_enabled, description, is_active) VALUES
            ('baseline-no-ai', FALSE, 'Baseline experiment with AI disabled', TRUE);
    END IF;
END $$;
