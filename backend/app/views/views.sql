-- Smart CDN Database Views
-- Exactly 3 views with JOINs and aggregations for dashboard and API queries

-- View 1: Cache Hit Ratio by Edge Region
-- Aggregates hit/miss statistics per edge node with region information
-- Used by: Dashboard metrics, Edge performance monitoring
CREATE OR REPLACE VIEW cache_hit_ratio_by_edge AS
SELECT 
    e.edge_id,
    e.region,
    COUNT(r.request_id) AS total_requests,
    COUNT(CASE WHEN r.is_cache_hit = TRUE THEN 1 END) AS cache_hits,
    COUNT(CASE WHEN r.is_cache_hit = FALSE THEN 1 END) AS cache_misses,
    CASE 
        WHEN COUNT(r.request_id) > 0 
        THEN ROUND(
            (COUNT(CASE WHEN r.is_cache_hit = TRUE THEN 1 END)::NUMERIC / COUNT(r.request_id)::NUMERIC) * 100, 
            2
        )
        ELSE 0 
    END AS hit_ratio_percent,
    ROUND(AVG(r.response_time_ms), 2) AS avg_response_time_ms,
    ROUND(AVG(CASE WHEN r.is_cache_hit = TRUE THEN r.response_time_ms END), 2) AS avg_hit_latency_ms,
    ROUND(AVG(CASE WHEN r.is_cache_hit = FALSE THEN r.response_time_ms END), 2) AS avg_miss_latency_ms,
    MAX(r.request_timestamp) AS last_request_time
FROM 
    edge_nodes e
LEFT JOIN 
    requests r ON e.edge_id = r.edge_id
WHERE 
    e.is_active = TRUE
GROUP BY 
    e.edge_id, e.region
ORDER BY 
    total_requests DESC;

-- View 2: Top Hot Content with Popularity Metrics
-- Aggregates request counts and popularity metrics per content item
-- Used by: Dashboard hot content list, AI prefetch candidate selection
CREATE OR REPLACE VIEW top_hot_content AS
SELECT 
    c.content_id,
    c.content_type,
    c.size_kb,
    c.category,
    COUNT(r.request_id) AS total_requests,
    COUNT(DISTINCT r.edge_id) AS edges_serving,
    COUNT(CASE WHEN r.is_cache_hit = TRUE THEN 1 END) AS cache_hits,
    COUNT(CASE WHEN r.is_cache_hit = FALSE THEN 1 END) AS cache_misses,
    CASE 
        WHEN COUNT(r.request_id) > 0 
        THEN ROUND(
            (COUNT(CASE WHEN r.is_cache_hit = TRUE THEN 1 END)::NUMERIC / COUNT(r.request_id)::NUMERIC) * 100, 
            2
        )
        ELSE 0 
    END AS hit_ratio_percent,
    ROUND(AVG(r.response_time_ms), 2) AS avg_response_time_ms,
    MAX(r.request_timestamp) AS last_request_time,
    MIN(r.request_timestamp) AS first_request_time,
    -- Calculate requests in last hour (for trending detection)
    COUNT(CASE 
        WHEN r.request_timestamp >= NOW() - INTERVAL '1 hour' 
        THEN 1 
    END) AS requests_last_hour,
    -- Calculate requests in last 24 hours
    COUNT(CASE 
        WHEN r.request_timestamp >= NOW() - INTERVAL '24 hours' 
        THEN 1 
    END) AS requests_last_24h
FROM 
    content c
LEFT JOIN 
    requests r ON c.content_id = r.content_id
GROUP BY 
    c.content_id, c.content_type, c.size_kb, c.category
HAVING 
    COUNT(r.request_id) > 0
ORDER BY 
    total_requests DESC,
    requests_last_hour DESC;

-- View 3: AI Decision Effectiveness Analysis
-- Compares AI predictions vs actual request patterns
-- Used by: Dashboard AI effectiveness metrics, Experiment comparison
CREATE OR REPLACE VIEW ai_decision_effectiveness AS
SELECT 
    ad.decision_id,
    ad.decision_type,
    ad.content_id,
    c.content_type,
    c.category,
    ad.edge_id,
    e.region,
    ad.predicted_popularity,
    ad.priority,
    ad.decision_timestamp,
    ad.applied_at,
    -- Actual requests after decision was made
    COUNT(r.request_id) AS actual_requests_after_decision,
    COUNT(CASE WHEN r.is_cache_hit = TRUE THEN 1 END) AS actual_cache_hits,
    COUNT(CASE WHEN r.is_cache_hit = FALSE THEN 1 END) AS actual_cache_misses,
    -- Prediction accuracy (for prefetch decisions)
    CASE 
        WHEN ad.decision_type = 'prefetch' AND ad.predicted_popularity > 0
        THEN ROUND(
            (COUNT(r.request_id)::NUMERIC / NULLIF(ad.predicted_popularity, 0)) * 100,
            2
        )
        ELSE NULL
    END AS prediction_accuracy_percent,
    -- Latency improvement (if decision was applied)
    CASE 
        WHEN ad.applied_at IS NOT NULL
        THEN ROUND(
            AVG(CASE 
                WHEN r.request_timestamp >= ad.applied_at AND r.is_cache_hit = TRUE 
                THEN r.response_time_ms 
            END) - 
            AVG(CASE 
                WHEN r.request_timestamp < ad.applied_at AND r.is_cache_hit = FALSE 
                THEN r.response_time_ms 
            END),
            2
        )
        ELSE NULL
    END AS latency_improvement_ms,
    -- Time window for analysis (requests within 1 hour after decision)
    COUNT(CASE 
        WHEN r.request_timestamp >= ad.decision_timestamp 
        AND r.request_timestamp <= ad.decision_timestamp + INTERVAL '1 hour'
        THEN 1 
    END) AS requests_in_window
FROM 
    ai_decisions ad
LEFT JOIN 
    content c ON ad.content_id = c.content_id
LEFT JOIN 
    edge_nodes e ON ad.edge_id = e.edge_id
LEFT JOIN 
    requests r ON ad.content_id = r.content_id 
        AND (ad.edge_id IS NULL OR ad.edge_id = r.edge_id)
        AND r.request_timestamp >= ad.decision_timestamp
GROUP BY 
    ad.decision_id, 
    ad.decision_type, 
    ad.content_id, 
    c.content_type, 
    c.category,
    ad.edge_id, 
    e.region,
    ad.predicted_popularity, 
    ad.priority, 
    ad.decision_timestamp, 
    ad.applied_at
ORDER BY 
    ad.decision_timestamp DESC,
    actual_requests_after_decision DESC;
