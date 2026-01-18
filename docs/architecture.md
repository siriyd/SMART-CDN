# Smart CDN Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Database Schema](#database-schema)
7. [API Design](#api-design)
8. [Caching Strategy](#caching-strategy)
9. [AI Integration](#ai-integration)
10. [Scalability Considerations](#scalability-considerations)

---

## System Overview

The Smart CDN is a distributed content delivery network that uses AI-driven caching to optimize content placement across edge nodes. The system consists of multiple microservices communicating via REST APIs, with PostgreSQL for structured data and Redis for edge cache simulation.

### Key Principles

- **Microservices Architecture:** Independent, scalable services
- **Separation of Concerns:** AI logic separated from business logic
- **Data-Driven Decisions:** AI analyzes patterns and makes intelligent caching decisions
- **A/B Testing:** Built-in experiment framework for performance evaluation
- **Real-time Monitoring:** Dashboard provides live metrics and visualization

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User/Client                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard (React)                    │
│                    Port: 3000                                   │
│  - Real-time metrics visualization                              │
│  - AI decisions monitoring                                      │
│  - Experiment management                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                        │
│                    Port: 8000                                   │
│  - Request routing                                              │
│  - Database operations                                          │
│  - AI engine coordination                                       │
│  - Metrics aggregation                                          │
└──────┬──────────────────────┬──────────────────────┬───────────┘
       │                      │                      │
       │ HTTP                 │ HTTP                 │ HTTP
       ▼                      ▼                      ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ AI Engine    │    │ Edge         │    │ PostgreSQL   │
│ (FastAPI)    │    │ Simulator    │    │ Database     │
│ Port: 8001   │    │ Port: 8002   │    │ Port: 5432   │
│              │    │              │    │              │
│ - Predictor  │    │ - Cache      │    │ - Requests   │
│ - Policy     │    │   lookup     │    │ - Content    │
│ - Decisions  │    │ - Origin     │    │ - Edges      │
│              │    │   fetch      │    │ - AI         │
│              │    │ - Metrics    │    │   decisions  │
│              │    │   logging    │    │ - Experiments│
└──────────────┘    └──────┬───────┘    └──────────────┘
                           │
                           │ Redis Protocol
                           ▼
                  ┌──────────────┐
                  │ Redis Cache  │
                  │ Port: 6379   │
                  │              │
                  │ - Edge caches│
                  │ - TTLs       │
                  │ - Keys:      │
                  │   edge:{id}: │
                  │   content:{id}│
                  └──────────────┘
```

---

## Component Details

### 1. Frontend Dashboard (React)

**Technology:** React 18, Vite, Tailwind CSS, Recharts

**Responsibilities:**
- User interface for monitoring and control
- Real-time metrics visualization
- AI decisions display
- Experiment management
- Authentication (JWT)

**Key Features:**
- Auto-refreshing dashboards (30s intervals)
- Interactive charts (hit/miss ratios, latency, traffic patterns)
- Experiment toggle (AI ON/OFF)
- Responsive design

**API Integration:**
- Communicates with Backend API via REST
- Uses axios for HTTP requests
- JWT token stored in localStorage

### 2. Backend API (FastAPI)

**Technology:** Python 3.10+, FastAPI, SQLAlchemy, Redis, httpx

**Responsibilities:**
- Request routing and handling
- Database operations (PostgreSQL)
- AI engine coordination
- Metrics aggregation
- Experiment management
- Authentication and authorization

**Key Modules:**
- `routes_metrics.py`: Metrics endpoints
- `routes_ai.py`: AI decision triggering
- `routes_experiments.py`: A/B testing
- `routes_requests.py`: Request logging
- `services/ai_client.py`: AI engine HTTP client
- `services/experiment_service.py`: Experiment management
- `db/postgres.py`: Database adapter

**API Endpoints:**
- `/api/v1/metrics/*`: Cache hit ratio, latency, popularity
- `/api/v1/ai/decide`: Trigger AI decisions
- `/api/v1/experiments/*`: Experiment management
- `/api/v1/requests/*`: Request logging and retrieval
- `/api/v1/edges/*`: Edge node information
- `/api/v1/content/*`: Content metadata

### 3. AI Engine (FastAPI Microservice)

**Technology:** Python 3.10+, FastAPI, NumPy (for forecasting)

**Responsibilities:**
- Popularity prediction using time-series forecasting
- Caching policy decisions (prefetch, evict, TTL)
- Decision generation based on request patterns

**Key Modules:**
- `predictor.py`: Exponential smoothing for popularity prediction
- `policy.py`: Caching policy logic (prefetch thresholds, eviction rules)
- `schemas.py`: Request/response data models

**Decision Types:**
1. **Prefetch:** Proactively cache popular content
2. **Evict:** Remove rarely-used content to free space
3. **TTL Update:** Adjust cache expiration based on predicted demand

**Algorithm:**
- Uses exponential smoothing (Holt-Winters method) for time-series forecasting
- Analyzes request patterns over sliding time windows
- Generates confidence scores for predictions
- Makes decisions based on cost/benefit analysis

### 4. Edge Simulator (FastAPI)

**Technology:** Python 3.10+, FastAPI, Redis

**Responsibilities:**
- Simulates edge node behavior
- Cache lookup (Redis)
- Origin server fallback
- Request metrics logging
- TTL management

**Edge Nodes:**
- `edge-us-east-1`: US East region
- `edge-us-west-1`: US West region
- `edge-eu-west-1`: EU West region

**Cache Key Pattern:**
```
edge:{edge_id}:content:{content_id}
```

**Behavior:**
1. Check Redis cache for content
2. If cache hit: return cached content immediately
3. If cache miss: fetch from origin (backend), cache it, then return
4. Log request to PostgreSQL with hit/miss status and latency

### 5. PostgreSQL Database

**Technology:** PostgreSQL 14+

**Schema:**
- **edge_nodes:** Edge node metadata (region, capacity, usage)
- **content:** Content metadata (type, size, category)
- **requests:** Request logs (content_id, edge_id, hit/miss, latency, timestamp)
- **ai_decisions:** AI-generated caching decisions
- **experiments:** A/B experiment configurations
- **metrics:** Pre-computed metrics (optional, for performance)
- **cache_state:** Current cache state tracking

**Views:**
1. `v_cache_hit_ratio_by_edge`: Aggregated hit ratio per edge
2. `v_top_hot_content`: Most popular content by request count
3. `v_ai_decision_effectiveness`: AI decision success metrics

**Indexes:**
- Optimized for time-range queries on requests
- Foreign key indexes for joins
- Composite indexes for common query patterns

### 6. Redis Cache

**Technology:** Redis 7+

**Usage:**
- Simulates edge node caches
- Per-edge isolation using key prefixes
- TTL-based expiration
- LRU/LFU eviction (when AI is disabled)

**Key Structure:**
```
edge:{edge_id}:content:{content_id} = content_data
edge:{edge_id}:access:{content_id} = timestamp (for LRU)
edge:{edge_id}:freq:{content_id} = count (for LFU)
```

**Operations:**
- GET: Cache lookup
- SETEX: Cache with TTL
- TTL: Check expiration
- DEL: Eviction
- KEYS: List cached content (for statistics)

---

## Data Flow

### Request Flow (Cache Hit)

```
1. User → Edge Simulator: GET /edge/{edge_id}/content/{content_id}
2. Edge Simulator → Redis: GET edge:{edge_id}:content:{content_id}
3. Redis → Edge Simulator: Content found (cache hit)
4. Edge Simulator → PostgreSQL: INSERT request log (is_cache_hit=true)
5. Edge Simulator → User: Return content (fast, ~20ms)
```

### Request Flow (Cache Miss)

```
1. User → Edge Simulator: GET /edge/{edge_id}/content/{content_id}
2. Edge Simulator → Redis: GET edge:{edge_id}:content:{content_id}
3. Redis → Edge Simulator: Not found (cache miss)
4. Edge Simulator → Backend: GET /api/v1/content/{content_id} (origin fetch)
5. Backend → Edge Simulator: Return content
6. Edge Simulator → Redis: SETEX edge:{edge_id}:content:{content_id} (cache it)
7. Edge Simulator → PostgreSQL: INSERT request log (is_cache_hit=false)
8. Edge Simulator → User: Return content (slower, ~80ms)
```

### AI Decision Flow

```
1. Backend → PostgreSQL: SELECT recent requests (last 60 minutes)
2. Backend → AI Engine: POST /decide (request logs, content metadata, edge constraints)
3. AI Engine: Analyze patterns, predict popularity, generate decisions
4. AI Engine → Backend: Return decisions (prefetch, evict, TTL updates)
5. Backend → PostgreSQL: INSERT ai_decisions
6. Backend → Redis: Apply decisions (prefetch content, evict content, update TTLs)
7. Backend → Frontend: Display decisions in dashboard
```

### Metrics Flow

```
1. Frontend → Backend: GET /api/v1/metrics/cache-hit-ratio
2. Backend → PostgreSQL: Query v_cache_hit_ratio_by_edge view
3. PostgreSQL → Backend: Return aggregated data
4. Backend → Frontend: Return JSON response
5. Frontend: Render charts and tables
```

---

## Technology Stack

### Frontend
- **React 18:** Modern UI framework
- **Vite:** Fast build tool and dev server
- **Tailwind CSS:** Utility-first CSS framework
- **Recharts:** Chart library for data visualization
- **Axios:** HTTP client
- **React Router:** Client-side routing

**Justification:**
- React provides component reusability and state management
- Vite offers fast HMR and build times
- Tailwind enables rapid UI development
- Recharts is lightweight and React-native

### Backend
- **FastAPI:** Modern Python web framework
- **SQLAlchemy:** ORM for database operations
- **Pydantic:** Data validation and settings
- **httpx:** Async HTTP client for AI engine communication
- **python-jose:** JWT token handling
- **passlib:** Password hashing

**Justification:**
- FastAPI provides automatic API documentation and async support
- SQLAlchemy offers database abstraction and migration support
- Pydantic ensures type safety and validation
- httpx supports async/await for non-blocking HTTP calls

### AI Engine
- **FastAPI:** Consistent API framework
- **NumPy:** Numerical computations (for forecasting)
- **Pydantic:** Request/response validation

**Justification:**
- FastAPI ensures consistent API design across services
- NumPy provides efficient numerical operations for time-series analysis
- Lightweight dependencies for fast startup

### Data Storage
- **PostgreSQL:** Relational database for structured data
- **Redis:** In-memory cache for edge simulation

**Justification:**
- PostgreSQL provides ACID guarantees and complex queries
- Redis offers sub-millisecond latency for cache operations
- Separation allows independent scaling

### Infrastructure
- **Docker:** Containerization
- **Docker Compose:** Multi-container orchestration
- **Locust:** Load testing

**Justification:**
- Docker ensures reproducible deployments
- Docker Compose simplifies multi-service management
- Locust provides realistic load testing scenarios

---

## Database Schema

### Core Tables

#### `edge_nodes`
Stores edge node metadata.

```sql
edge_id (PK) | region | cache_capacity_mb | current_usage_mb | is_active
```

#### `content`
Stores content metadata.

```sql
content_id (PK) | content_type | size_kb | category
```

#### `requests`
Stores request logs (time-series data).

```sql
request_id (PK) | content_id (FK) | edge_id (FK) | is_cache_hit | 
response_time_ms | request_timestamp | experiment_id (FK)
```

#### `ai_decisions`
Stores AI-generated caching decisions.

```sql
decision_id (PK) | decision_type | content_id (FK) | edge_id (FK) | 
ttl_seconds | priority | decision_timestamp | applied_at | experiment_id (FK)
```

#### `experiments`
Stores A/B experiment configurations.

```sql
experiment_id (PK) | experiment_name | ai_enabled | start_time | 
end_time | is_active | description
```

### Views

#### `v_cache_hit_ratio_by_edge`
Aggregates cache hit ratio per edge.

```sql
SELECT 
    e.edge_id,
    e.region,
    COUNT(r.request_id) as total_requests,
    SUM(CASE WHEN r.is_cache_hit THEN 1 ELSE 0 END) as cache_hits,
    SUM(CASE WHEN NOT r.is_cache_hit THEN 1 ELSE 0 END) as cache_misses,
    (SUM(CASE WHEN r.is_cache_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(r.request_id)) as hit_ratio_percent
FROM edge_nodes e
LEFT JOIN requests r ON e.edge_id = r.edge_id
GROUP BY e.edge_id, e.region;
```

#### `v_top_hot_content`
Identifies most popular content.

```sql
SELECT 
    c.content_id,
    c.content_type,
    COUNT(r.request_id) as total_requests,
    (SUM(CASE WHEN r.is_cache_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(r.request_id)) as hit_ratio_percent
FROM content c
JOIN requests r ON c.content_id = r.content_id
GROUP BY c.content_id, c.content_type
ORDER BY total_requests DESC;
```

#### `v_ai_decision_effectiveness`
Measures AI decision success.

```sql
SELECT 
    ad.decision_type,
    COUNT(ad.decision_id) as total_decisions,
    COUNT(CASE WHEN ad.applied_at IS NOT NULL THEN 1 END) as applied_decisions,
    AVG(r.response_time_ms) as avg_latency_after_decision
FROM ai_decisions ad
LEFT JOIN requests r ON ad.content_id = r.content_id 
    AND r.request_timestamp > ad.applied_at
GROUP BY ad.decision_type;
```

---

## API Design

### RESTful Principles

- **Resource-based URLs:** `/api/v1/edges`, `/api/v1/content`
- **HTTP methods:** GET (read), POST (create), PUT (update), DELETE (remove)
- **Status codes:** 200 (success), 201 (created), 404 (not found), 500 (error)
- **JSON responses:** Consistent structure with `status`, `data`, `count` fields

### Authentication

- **JWT tokens:** Stateless authentication
- **Bearer token:** `Authorization: Bearer <token>`
- **Token expiration:** 30 minutes
- **Public endpoints:** Experiments endpoints (for demo purposes)

### Error Handling

- **Structured errors:** `{"detail": "Error message"}`
- **Validation errors:** Pydantic provides automatic validation
- **Database errors:** Caught and returned as 500 with details
- **Logging:** All errors logged with stack traces

---

## Caching Strategy

### AI-Enabled Mode

1. **Prefetch:** AI predicts popular content and proactively caches it
2. **Eviction:** AI identifies rarely-used content and evicts it
3. **TTL Tuning:** AI adjusts TTLs based on predicted demand patterns

### Baseline Mode (AI Disabled)

1. **LRU (Least Recently Used):** Evicts content not accessed recently
2. **LFU (Least Frequently Used):** Evicts content with lowest access frequency
3. **Fixed TTL:** Default 1-hour expiration

### Cache Key Design

```
edge:{edge_id}:content:{content_id}
```

- **Isolation:** Each edge has separate cache namespace
- **Collision-free:** Content IDs are unique
- **TTL:** Per-key expiration based on AI decisions or defaults

---

## AI Integration

### Prediction Algorithm

**Exponential Smoothing (Holt-Winters):**

1. **Single Exponential Smoothing:** For content with limited history
   - Formula: `S_t = α * X_t + (1-α) * S_{t-1}`
   - α (alpha) = 0.3 (smoothing factor)

2. **Double Exponential Smoothing:** For content with trend
   - Accounts for increasing/decreasing popularity

3. **Confidence Scoring:**
   - High confidence: Multiple requests, clear pattern
   - Low confidence: Single request, no pattern

### Decision Logic

**Prefetch Decision:**
- Predicted requests > threshold (default: 2)
- Confidence > threshold (default: 0.2)
- Content size < edge free capacity

**Eviction Decision:**
- Predicted requests < threshold
- Cache capacity exceeded
- Low priority content

**TTL Update:**
- Increase TTL for high-demand content
- Decrease TTL for low-demand content
- Bounded by min/max TTL constraints

---

## Scalability Considerations

### Horizontal Scaling

- **Backend API:** Stateless, can run multiple instances behind load balancer
- **AI Engine:** Stateless, can scale independently based on decision load
- **Edge Simulators:** Can add more edge nodes without code changes
- **PostgreSQL:** Can use read replicas for metrics queries
- **Redis:** Can use Redis Cluster for distributed caching

### Performance Optimizations

- **Database Indexes:** Optimized for time-range queries
- **View Materialization:** Pre-computed aggregations
- **Connection Pooling:** SQLAlchemy connection pool
- **Async Operations:** FastAPI async/await for non-blocking I/O
- **Caching:** Redis for edge caches, in-memory caching for frequent queries

### Limitations

- **Single PostgreSQL instance:** No replication in current setup
- **Single Redis instance:** No clustering (acceptable for demo)
- **AI Engine:** Single instance (can be scaled)
- **Edge Simulator:** Simulated, not real edge nodes

### Future Improvements

1. **Kubernetes Deployment:** Container orchestration
2. **Database Replication:** Read replicas for metrics
3. **Redis Cluster:** Distributed caching
4. **Message Queue:** Async decision processing (RabbitMQ/Kafka)
5. **CDN Integration:** Real edge nodes (Cloudflare, AWS CloudFront)
6. **Advanced ML:** LSTM/Transformer models for better predictions
7. **Real-time Streaming:** Kafka for request stream processing

---

## Security Considerations

### Current Implementation

- **JWT Authentication:** For dashboard access
- **CORS:** Configured for frontend origin
- **SQL Injection:** Prevented by SQLAlchemy ORM
- **Input Validation:** Pydantic models validate all inputs

### Production Recommendations

- **HTTPS:** Encrypt all traffic
- **Rate Limiting:** Prevent abuse
- **API Keys:** For service-to-service communication
- **Secrets Management:** Environment variables or secret managers
- **Audit Logging:** Track all administrative actions
- **Network Isolation:** Private networks for service communication

---

## Deployment

### Docker Compose

All services defined in `docker-compose.yml`:
- PostgreSQL container
- Redis container
- Backend container
- AI Engine container
- Edge Simulator container
- Frontend container (optional)

### Environment Variables

Configuration via `.env` file:
- Database credentials
- Redis connection
- API URLs
- Secret keys

### Local Development

```bash
# Start infrastructure
docker-compose up postgres redis

# Start services
cd backend && uvicorn app.main:app --reload
cd ai-engine && uvicorn ai.main:app --reload
cd edge-sim && uvicorn edge.main:app --reload
cd frontend && npm run dev
```

---

## Monitoring and Observability

### Metrics Collected

- **Request Metrics:** Count, latency, cache hit/miss
- **Cache Metrics:** Hit ratio, eviction rate, TTL distribution
- **AI Metrics:** Decision count, prediction accuracy, application success
- **System Metrics:** Response times, error rates, throughput

### Logging

- **Structured Logging:** JSON format for parsing
- **Log Levels:** DEBUG, INFO, WARNING, ERROR
- **Error Tracking:** Full stack traces with `exc_info=True`

### Dashboard

- **Real-time Updates:** 30-second refresh intervals
- **Visualizations:** Charts for trends and patterns
- **Alerts:** Can be extended for threshold-based alerts

---

## Conclusion

The Smart CDN architecture demonstrates:
- **Modern distributed systems** principles
- **Microservices** design patterns
- **AI/ML integration** for intelligent automation
- **Comprehensive evaluation** through A/B testing
- **Production-ready** code quality and practices

This architecture is scalable, maintainable, and suitable for real-world deployment with appropriate infrastructure enhancements.
