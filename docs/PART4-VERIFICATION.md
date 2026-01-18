# Part 4: Edge Cache Simulation Verification Guide

## What Was Created

### 1. Redis Cache Adapter (`edge-sim/edge/cache.py`)

- Redis-based edge cache with TTL support
- Cache operations: get, set, delete, exists, update_ttl
- Cache statistics and management
- Per-edge cache isolation using key prefixes

### 2. Origin Client (`edge-sim/edge/origin_client.py`)

- HTTP client to fetch content from backend origin
- Health checking
- Error handling and timeouts

### 3. Metrics Logger (`edge-sim/edge/metrics.py`)

- Logs request metrics to backend database
- Async logging to avoid blocking requests
- Tracks cache hits/misses and response times

### 4. Edge Simulator API (`edge-sim/edge/main.py`)

- Main CDN request endpoint: `/api/v1/content/{content_id}`
- Cache statistics endpoint
- Cache management endpoints (evict, prefetch, update TTL)
- Multi-region support (us-east, us-west, eu-west)

### 5. Request Logging API (`backend/app/api/routes_requests.py`)

- Endpoint to log requests from edge simulators
- Stores requests in PostgreSQL database

### 6. Traffic Simulation Script (`edge-sim/scripts/simulate_traffic.py`)

- Generates requests to test cache behavior
- Configurable request count, delay, content IDs
- Reports cache hit ratio and response times

## How to Verify Part 4

### Step 1: Start Infrastructure Services

```bash
cd smart-cdn
docker-compose up postgres redis -d
```

Wait 5 seconds for services to be ready.

### Step 2: Start Backend (for origin server)

```bash
cd smart-cdn/backend

# Set environment variables
export POSTGRES_USER=cdn_admin
export POSTGRES_PASSWORD=cdn_secure_pass_2024
export POSTGRES_DB=smart_cdn_db
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Seed Sample Content (Manual SQL)

Since content CRUD is not complete, insert content manually:

```bash
docker exec -it smart-cdn-postgres psql -U cdn_admin -d smart_cdn_db
```

```sql
INSERT INTO content (content_id, content_type, size_kb, category) VALUES
    ('video-001', 'video', 5000, 'entertainment'),
    ('image-001', 'image', 200, 'news'),
    ('html-001', 'html', 50, 'news')
ON CONFLICT (content_id) DO NOTHING;
```

### Step 4: Start Edge Simulator

```bash
cd smart-cdn/edge-sim

# Set environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379
export ORIGIN_SERVER_URL=http://localhost:8000
export EDGE_REGIONS=us-east,us-west,eu-west

# Start edge simulator
python -m uvicorn edge.main:app --host 0.0.0.0 --port 8002 --reload
```

### Step 5: Test Edge Cache Health

```bash
curl http://localhost:8002/health
```

**Expected**:

```json
{
  "status": "healthy",
  "service": "edge-sim",
  "version": "1.0.0",
  "redis": "connected",
  "origin": "connected"
}
```

### Step 6: Test Cache Miss (First Request)

```bash
curl http://localhost:8002/api/v1/content/video-001 \
  -H "X-Edge-Id: edge-us-east"
```

**Expected**:

```json
{
  "content_id": "video-001",
  "edge_id": "edge-us-east",
  "is_cache_hit": false,
  "response_time_ms": 200,
  "content_data": {
    "content_id": "video-001",
    "content_type": "video",
    "size_kb": 5000,
    "category": "entertainment"
  },
  "cache_ttl_seconds": 3600
}
```

Note: `is_cache_hit: false` and `response_time_ms: 200` (cache miss latency)

### Step 7: Test Cache Hit (Second Request)

```bash
curl http://localhost:8002/api/v1/content/video-001 \
  -H "X-Edge-Id: edge-us-east"
```

**Expected**:

```json
{
  "content_id": "video-001",
  "edge_id": "edge-us-east",
  "is_cache_hit": true,
  "response_time_ms": 10,
  "content_data": {...},
  "cache_ttl_seconds": 3600
}
```

Note: `is_cache_hit: true` and `response_time_ms: 10` (cache hit latency)

### Step 8: Test Different Edges

```bash
# Request to us-west edge (cache miss)
curl http://localhost:8002/api/v1/content/video-001 \
  -H "X-Edge-Id: edge-us-west"

# Request to us-west edge again (cache hit)
curl http://localhost:8002/api/v1/content/video-001 \
  -H "X-Edge-Id: edge-us-west"
```

Each edge maintains its own cache.

### Step 9: Check Cache Statistics

```bash
curl http://localhost:8002/api/v1/edges/edge-us-east/cache/stats
```

**Expected**:

```json
{
  "edge_id": "edge-us-east",
  "cached_items": 1,
  "estimated_size_bytes": 1234,
  "estimated_size_mb": 0.0,
  "capacity_mb": 100
}
```

### Step 10: Test Prefetch

```bash
curl -X POST "http://localhost:8002/api/v1/edges/edge-eu-west/cache/prefetch?content_id=image-001"
```

**Expected**:

```json
{
  "status": "success",
  "message": "Prefetched image-001 into edge-eu-west",
  "ttl_seconds": 3600
}
```

### Step 11: Test Evict

```bash
curl -X DELETE "http://localhost:8002/api/v1/edges/edge-us-east/cache/video-001"
```

**Expected**:

```json
{
  "status": "success",
  "message": "Evicted video-001 from edge-us-east"
}
```

### Step 12: Verify Request Logging

Check that requests are logged to database:

```bash
curl http://localhost:8000/api/v1/requests?limit=10
```

Should show logged requests with cache hit/miss information.

### Step 13: Run Traffic Simulation

```bash
cd smart-cdn/edge-sim/scripts
python simulate_traffic.py -n 50 -d 50 -v
```

**Expected output**:

```
Starting traffic simulation:
  Requests: 50
  Content IDs: 9
  Edge IDs: 3
  Delay: 50ms between requests

✓ video-001 @ edge-us-east: MISS (200ms)
✓ video-001 @ edge-us-east: HIT (10ms)
✓ image-001 @ edge-us-west: MISS (200ms)
...

==================================================
Simulation Summary
==================================================
Total requests: 50
Cache hits: 25 (50.0%)
Cache misses: 25 (50.0%)
Errors: 0
Average response time: 105.00ms
==================================================
```

### Step 14: Verify Redis Cache

```bash
# Connect to Redis
docker exec -it smart-cdn-redis redis-cli

# List cache keys
KEYS edge:*

# Get a cached item
GET edge:edge-us-east:content:video-001

# Check TTL
TTL edge:edge-us-east:content:video-001
```

## Expected Behavior

### Cache Miss Flow

1. Request arrives at edge
2. Check Redis cache → Not found
3. Fetch from origin (backend)
4. Store in Redis with TTL
5. Log request to database (is_cache_hit=false)
6. Return content (response_time_ms=200)

### Cache Hit Flow

1. Request arrives at edge
2. Check Redis cache → Found
3. Log request to database (is_cache_hit=true)
4. Return content (response_time_ms=10)

## Common Issues & Fixes

### Issue: "Origin client not initialized"

**Solution**: Check edge simulator startup logs. Origin client should initialize on startup.

### Issue: "Connection refused" to Redis

**Solution**:

- Check Redis is running: `docker-compose ps redis`
- Verify `REDIS_HOST=localhost` when running outside Docker

### Issue: "Content not found" errors

**Solution**:

- Ensure content exists in database (seed content)
- Check backend is running and accessible

### Issue: Requests not being logged

**Solution**:

- Check backend `/api/v1/requests/log` endpoint exists
- Check edge simulator logs for errors
- Verify database connection in backend

### Issue: Cache not working (always misses)

**Solution**:

- Check Redis connection in edge simulator
- Verify Redis keys: `docker exec -it smart-cdn-redis redis-cli KEYS edge:*`
- Check TTL values are set correctly

## Verification Checklist

- [ ] Redis container is running
- [ ] Backend is running and accessible
- [ ] Edge simulator starts without errors
- [ ] Health check shows Redis and origin connected
- [ ] First request is cache miss (200ms)
- [ ] Second request is cache hit (10ms)
- [ ] Different edges have separate caches
- [ ] Cache statistics endpoint works
- [ ] Prefetch endpoint works
- [ ] Evict endpoint works
- [ ] Requests are logged to database
- [ ] Traffic simulation shows cache hits/misses
- [ ] Redis contains cached items with TTLs

## API Endpoints Summary

### Edge Simulator

| Endpoint                                         | Method | Description                   |
| ------------------------------------------------ | ------ | ----------------------------- |
| `/health`                                        | GET    | Health check                  |
| `/api/v1/content/{content_id}`                   | GET    | Get content (cache or origin) |
| `/api/v1/edges/{edge_id}/cache/stats`            | GET    | Cache statistics              |
| `/api/v1/edges/{edge_id}/cache/{content_id}`     | DELETE | Evict content                 |
| `/api/v1/edges/{edge_id}/cache/prefetch`         | POST   | Prefetch content              |
| `/api/v1/edges/{edge_id}/cache/{content_id}/ttl` | PUT    | Update TTL                    |

### Backend

| Endpoint               | Method | Description         |
| ---------------------- | ------ | ------------------- |
| `/api/v1/requests/log` | POST   | Log request metrics |
| `/api/v1/requests`     | GET    | Get logged requests |

## Next Steps

✅ **Part 4 Complete**

After verification:

- Edge cache simulation is working
- Redis caching with TTL is functional
- Cache hits are faster than misses
- Requests are logged to database
- Ready for Part 5 (AI Engine Integration)

---

**Status**: Edge cache simulation ready 🚀
