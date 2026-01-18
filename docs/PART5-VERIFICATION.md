# Part 5: AI Engine Integration Verification Guide

## What Was Created

### 1. AI Decision Schemas (`ai-engine/ai/schemas.py`)
- Pydantic models for structured AI outputs
- `PrefetchItem`, `EvictionItem`, `TTLUpdateItem`
- `PopularityForecast`, `AIDecisionResponse`
- Full validation with field constraints

### 2. Popularity Predictor (`ai-engine/ai/predictor.py`)
- Local time-series forecasting
- Exponential smoothing with trend detection
- Metadata-aware predictions
- Confidence scoring

### 3. Caching Policy Engine (`ai-engine/ai/policy.py`)
- Prefetch decision logic
- Eviction decision logic
- TTL update logic
- Capacity-aware decisions

### 4. AI Engine API (`ai-engine/ai/main.py`)
- `/decide` endpoint for generating decisions
- Input validation and error handling
- Returns structured JSON decisions

### 5. Backend AI Client (`backend/app/services/ai_client.py`)
- HTTP client for calling AI engine
- Health checking
- Error handling

### 6. CDN Logic Service (`backend/app/services/cdn_logic.py`)
- Applies AI decisions to edge caches
- Prefetch, eviction, TTL update operations
- Integration with edge simulator

### 7. AI Decision API Routes (`backend/app/api/routes_ai.py`)
- `/api/v1/ai/decide` - Trigger AI decisions
- `/api/v1/ai/decisions` - Get stored decisions
- Stores decisions in PostgreSQL
- Applies decisions to Redis caches

## How to Verify Part 5

### Step 1: Start All Services

```bash
cd smart-cdn

# Start infrastructure
docker-compose up postgres redis -d

# Start backend (Terminal 1)
cd backend
export POSTGRES_HOST=localhost
python -m uvicorn app.main:app --port 8000

# Start AI engine (Terminal 2)
cd ai-engine
python -m uvicorn ai.main:app --port 8001

# Start edge simulator (Terminal 3)
cd edge-sim
export REDIS_HOST=localhost
export ORIGIN_SERVER_URL=http://localhost:8000
python -m uvicorn edge.main:app --port 8002
```

### Step 2: Seed Content and Generate Traffic

```bash
# Insert content
docker exec -it smart-cdn-postgres psql -U cdn_admin -d smart_cdn_db -c "
INSERT INTO content (content_id, content_type, size_kb, category) VALUES
    (1, 'video', 5000, 'entertainment'),
    (2, 'image', 200, 'news'),
    (3, 'html', 50, 'news')
ON CONFLICT (content_id) DO NOTHING;
"

# Generate some traffic to create request logs
cd edge-sim/scripts
python simulate_traffic.py -n 30 -d 100
```

### Step 3: Test AI Engine Health

```bash
curl http://localhost:8001/health
```

**Expected**:
```json
{
  "status": "healthy",
  "service": "ai-engine",
  "version": "1.0.0"
}
```

### Step 4: Test AI Decision Endpoint Directly

```bash
curl -X POST http://localhost:8001/decide \
  -H "Content-Type: application/json" \
  -d '{
    "request_logs": [
      {
        "content_id": "1",
        "request_timestamp": "2024-01-01T12:00:00Z",
        "is_cache_hit": false
      },
      {
        "content_id": "1",
        "request_timestamp": "2024-01-01T12:05:00Z",
        "is_cache_hit": true
      }
    ],
    "content_metadata": [
      {
        "content_id": "1",
        "content_type": "video",
        "size_kb": 5000,
        "category": "entertainment"
      }
    ],
    "edge_constraints": [
      {
        "edge_id": "edge-us-east",
        "cache_capacity_mb": 100,
        "current_usage_mb": 10
      }
    ],
    "time_window_minutes": 60
  }'
```

**Expected**: JSON response with:
- `popularity_forecast`: List of predictions
- `prefetch_plan`: List of prefetch decisions
- `eviction_plan`: List of eviction decisions
- `ttl_updates`: List of TTL updates
- `model_mode`: "local"

### Step 5: Trigger AI Decisions via Backend

```bash
curl -X POST "http://localhost:8000/api/v1/ai/decide?time_window_minutes=60&apply_decisions=true"
```

**Expected**:
```json
{
  "status": "success",
  "decisions": {
    "popularity_forecast": [...],
    "prefetch_plan": [...],
    "eviction_plan": [...],
    "ttl_updates": [...],
    "model_mode": "local"
  },
  "application_results": {
    "prefetch": {"success": X, "failed": Y},
    "eviction": {"success": X, "failed": Y},
    "ttl_updates": {"success": X, "failed": Y}
  },
  "decision_id": 1
}
```

### Step 6: Verify Decisions Stored in Database

```bash
curl http://localhost:8000/api/v1/ai/decisions?limit=10
```

Should return stored AI decisions.

### Step 7: Verify Prefetch Applied

After triggering decisions, check if content was prefetched:

```bash
# Check cache stats
curl http://localhost:8002/api/v1/edges/edge-us-east/cache/stats

# Try to get prefetched content (should be cache hit)
curl http://localhost:8002/api/v1/content/1 -H "X-Edge-Id: edge-us-east"
```

### Step 8: Test with More Traffic

```bash
# Generate more traffic
cd edge-sim/scripts
python simulate_traffic.py -n 50 -d 50

# Trigger AI decisions again
curl -X POST "http://localhost:8000/api/v1/ai/decide?apply_decisions=true"
```

### Step 9: Check Database for Stored Decisions

```bash
docker exec -it smart-cdn-postgres psql -U cdn_admin -d smart_cdn_db -c "
SELECT decision_id, decision_type, content_id, edge_id, 
       predicted_popularity, decision_timestamp, applied_at
FROM ai_decisions
ORDER BY decision_timestamp DESC
LIMIT 10;
"
```

## Expected Behavior

### AI Decision Flow

1. Backend collects recent request logs
2. Backend fetches content metadata and edge constraints
3. Backend calls AI engine `/decide` endpoint
4. AI engine generates:
   - Popularity forecasts
   - Prefetch plan
   - Eviction plan
   - TTL updates
5. Backend stores decisions in PostgreSQL
6. Backend applies decisions to edge caches (if `apply_decisions=true`)
7. Edge caches are updated (prefetch/evict/ttl)

### Decision Logic

- **Prefetch**: Content with predicted requests > threshold (default 5)
- **Evict**: Content with predicted requests <= threshold (default 0)
- **TTL Update**: Adjust TTL based on predicted popularity

## Common Issues & Fixes

### Issue: "AI engine not reachable"
**Solution**: 
- Check AI engine is running: `curl http://localhost:8001/health`
- Verify `AI_ENGINE_URL` in backend config

### Issue: "No request logs found"
**Solution**:
- Generate traffic first: `python simulate_traffic.py -n 30`
- Check database has requests: `SELECT COUNT(*) FROM requests;`

### Issue: "Decisions not being applied"
**Solution**:
- Check edge simulator is running
- Verify `apply_decisions=true` in request
- Check backend logs for errors

### Issue: "Invalid decision format"
**Solution**:
- Check AI engine returns valid JSON
- Verify Pydantic schemas match
- Check AI engine logs for errors

## Verification Checklist

- [ ] AI engine starts without errors
- [ ] `/decide` endpoint returns structured decisions
- [ ] Backend can call AI engine successfully
- [ ] Decisions are stored in PostgreSQL
- [ ] Prefetch decisions are applied to edge caches
- [ ] Eviction decisions are applied to edge caches
- [ ] TTL updates are applied to edge caches
- [ ] Popularity forecasts are generated
- [ ] Decision validation works (Pydantic schemas)
- [ ] Application results are returned

## API Endpoints Summary

### AI Engine

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/decide` | POST | Generate caching decisions |

### Backend

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ai/decide` | POST | Trigger AI decisions and apply |
| `/api/v1/ai/decisions` | GET | Get stored AI decisions |

## Next Steps

✅ **Part 5 Complete**

After verification:
- AI engine generates caching decisions
- Decisions are stored in PostgreSQL
- Decisions are applied to Redis caches
- Ready for Part 6 (Frontend Dashboard)

---

**Status**: AI engine integration ready 🚀

