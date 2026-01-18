# Part 3: Backend Database Adapter Verification Guide

## What Was Created

### 1. Updated Database Adapter (`backend/app/db/postgres.py`)

- Updated to use actual view names:
  - `v_cache_hit_ratio`
  - `v_latency_by_edge`
  - `v_content_popularity`
- Helper functions for each view
- Connection health checking

### 2. FastAPI Integration (`backend/app/main.py`)

- Database connection on startup
- Health check endpoint with DB status
- Database status endpoint (`/api/v1/db/status`)
- Integrated API routes

### 3. API Routes

- **`routes_metrics.py`**: Metrics endpoints for all 3 views
- **`routes_edges.py`**: Edge node information endpoints
- **`routes_content.py`**: Content information endpoints

## How to Verify Part 3

### Step 1: Ensure PostgreSQL is Running

```bash
cd smart-cdn
docker-compose up postgres -d
```

Wait 5 seconds for PostgreSQL to be ready.

### Step 2: Start Backend (Without Docker)

**Option A: Using Python directly (if installed)**

```bash
cd smart-cdn/backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Set environment variables
export POSTGRES_USER=cdn_admin
export POSTGRES_PASSWORD=cdn_secure_pass_2024
export POSTGRES_DB=smart_cdn_db
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

# Run backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option B: Using Docker (if backend service is in docker-compose)**

```bash
# If you have backend service in docker-compose.yml
docker-compose up backend -d
```

### Step 3: Test Health Endpoint

```bash
# Using curl
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "backend",
#   "version": "1.0.0",
#   "database": "connected"
# }
```

### Step 4: Test Database Status Endpoint

```bash
curl http://localhost:8000/api/v1/db/status

# Expected response:
# {
#   "status": "connected",
#   "postgres_version": "PostgreSQL 15.x",
#   "database": "smart_cdn_db",
#   "tables": 6,
#   "views": 3
# }
```

### Step 5: Test Metrics Endpoints

```bash
# Cache hit ratio view
curl http://localhost:8000/api/v1/metrics/cache-hit-ratio

# Latency by edge view
curl http://localhost:8000/api/v1/metrics/latency

# Content popularity view
curl http://localhost:8000/api/v1/metrics/content-popularity?limit=10

# All metrics summary
curl http://localhost:8000/api/v1/metrics/summary
```

**Expected**: All endpoints should return JSON with `status: "success"` and empty or populated `data` arrays.

### Step 6: Test Edge Endpoints

```bash
# Get all edges
curl http://localhost:8000/api/v1/edges

# Get specific edge
curl http://localhost:8000/api/v1/edges/edge-us-east

# Get edge statistics
curl http://localhost:8000/api/v1/edges/edge-us-east/stats
```

**Expected**: Should return edge node information (3 default edges should exist).

### Step 7: Test Content Endpoints

```bash
# Get all content (will be empty initially)
curl http://localhost:8000/api/v1/content

# Get popular content
curl http://localhost:8000/api/v1/content/popular?limit=10
```

**Expected**: Should return empty arrays initially (no content inserted yet).

### Step 8: Verify View Queries Work

Test that the views can be queried directly:

```bash
# Using psql
docker exec -it smart-cdn-postgres psql -U cdn_admin -d smart_cdn_db

# In psql:
SELECT * FROM v_cache_hit_ratio;
SELECT * FROM v_latency_by_edge;
SELECT * FROM v_content_popularity LIMIT 5;
```

All queries should execute without errors (may return empty results).

### Step 9: Check API Documentation

Open browser: http://localhost:8000/docs

You should see:

- Swagger UI with all endpoints
- `/health` endpoint
- `/api/v1/db/status` endpoint
- `/api/v1/metrics/*` endpoints
- `/api/v1/edges/*` endpoints
- `/api/v1/content/*` endpoints

## Expected API Responses

### Health Check

```json
{
  "status": "healthy",
  "service": "backend",
  "version": "1.0.0",
  "database": "connected"
}
```

### Database Status

```json
{
  "status": "connected",
  "postgres_version": "PostgreSQL 15.4",
  "database": "smart_cdn_db",
  "tables": 6,
  "views": 3
}
```

### Metrics Endpoint (Example)

```json
{
  "status": "success",
  "count": 3,
  "data": [
    {
      "edge_id": "edge-us-east",
      "region": "us-east",
      "total_requests": 0,
      "cache_hits": 0,
      "cache_misses": 0,
      "hit_ratio_percent": 0.0
    }
  ]
}
```

## Common Issues & Fixes

### Issue: "Connection refused" or "Can't connect to database"

**Solution**:

- Check PostgreSQL is running: `docker-compose ps`
- Verify connection string in `.env` or environment variables
- Check `POSTGRES_HOST` is `localhost` (not `postgres`) when running outside Docker

### Issue: "relation does not exist" or "view does not exist"

**Solution**:

- Verify views exist: `docker exec -it smart-cdn-postgres psql -U cdn_admin -d smart_cdn_db -c "\dv"`
- Should show: `v_cache_hit_ratio`, `v_latency_by_edge`, `v_content_popularity`
- If missing, check `views.sql` was loaded correctly

### Issue: "Module not found" errors

**Solution**:

- Install dependencies: `pip install -r requirements.txt`
- Check Python path: `python -c "import app.db.postgres"`

### Issue: "Port 8000 already in use"

**Solution**:

- Change port in `uvicorn` command: `--port 8001`
- Or stop other service using port 8000

## Verification Checklist

- [ ] PostgreSQL container is running
- [ ] Backend starts without errors
- [ ] `/health` endpoint returns `"database": "connected"`
- [ ] `/api/v1/db/status` shows correct table/view counts
- [ ] All 3 metrics endpoints return JSON (even if empty)
- [ ] Edge endpoints return 3 default edges
- [ ] Content endpoints return JSON (even if empty)
- [ ] Swagger UI accessible at `/docs`
- [ ] No database connection errors in logs

## API Endpoints Summary

| Endpoint                             | Method | Description                 |
| ------------------------------------ | ------ | --------------------------- |
| `/health`                            | GET    | Health check with DB status |
| `/api/v1/db/status`                  | GET    | Detailed database status    |
| `/api/v1/metrics/cache-hit-ratio`    | GET    | Cache hit ratio by edge     |
| `/api/v1/metrics/latency`            | GET    | Latency by edge             |
| `/api/v1/metrics/content-popularity` | GET    | Content popularity metrics  |
| `/api/v1/metrics/summary`            | GET    | All metrics summary         |
| `/api/v1/edges`                      | GET    | List all edge nodes         |
| `/api/v1/edges/{edge_id}`            | GET    | Get specific edge           |
| `/api/v1/edges/{edge_id}/stats`      | GET    | Edge statistics from views  |
| `/api/v1/content`                    | GET    | List content items          |
| `/api/v1/content/{content_id}`       | GET    | Get specific content        |
| `/api/v1/content/popular`            | GET    | Popular content from view   |

## Next Steps

✅ **Part 3 Complete**

After verification:

- Backend is connected to PostgreSQL
- All 3 views are accessible via API
- Ready for Part 4 (Edge Cache Simulation)

---

**Status**: Backend database adapter ready 🚀
