# Part 2: Database Layer Verification Guide

## What Was Created

### 1. Database Schema (`backend/app/db/schema.sql`)
- **7 normalized tables**:
  - `edge_nodes` - Edge cache node information
  - `content` - Content metadata (type, size, category)
  - `requests` - Request logs with hit/miss data
  - `ai_decisions` - AI-generated caching decisions
  - `experiments` - A/B experiment configurations
  - `metrics` - Pre-computed metrics aggregations
  - `cache_state` - Current cache state at each edge
- **Foreign keys** and **indexes** for performance
- **Default data**: 3 edge nodes (us-east, us-west, eu-west) and baseline experiment

### 2. Database Views (`backend/app/views/views.sql`)
- **View 1**: `cache_hit_ratio_by_edge` - Hit ratio statistics per edge with JOINs
- **View 2**: `top_hot_content` - Popular content with request aggregations
- **View 3**: `ai_decision_effectiveness` - AI prediction accuracy analysis

### 3. PostgreSQL Adapter (`backend/app/db/postgres.py`)
- SQLAlchemy engine and session management
- `get_db()` dependency for FastAPI routes
- Helper functions to query views
- Connection health checking

### 4. SQLAlchemy Models (`backend/app/db/models.py`)
- ORM models matching schema
- Relationships between tables
- Type-safe database operations

## How to Verify Part 2

### Step 1: Start PostgreSQL Only

```bash
cd smart-cdn
docker-compose up postgres -d
```

Wait 5-10 seconds for PostgreSQL to initialize.

### Step 2: Connect to PostgreSQL

**Option A: Using Docker exec**
```bash
docker exec -it smart-cdn-postgres psql -U cdn_admin -d smart_cdn_db
```

**Option B: Using psql from host (if installed)**
```bash
psql -h localhost -p 5432 -U cdn_admin -d smart_cdn_db
# Password: cdn_secure_pass_2024
```

### Step 3: Verify Tables

```sql
-- List all tables
\dt

-- Expected output:
--  public | ai_decisions      | table | cdn_admin
--  public | cache_state       | table | cdn_admin
--  public | content           | table | cdn_admin
--  public | edge_nodes        | table | cdn_admin
--  public | experiments       | table | cdn_admin
--  public | metrics           | table | cdn_admin
--  public | requests          | table | cdn_admin
```

### Step 4: Verify Default Data

```sql
-- Check edge nodes
SELECT * FROM edge_nodes;

-- Expected: 3 rows (us-east, us-west, eu-west)

-- Check experiments
SELECT * FROM experiments;

-- Expected: 1 row (baseline-no-ai)
```

### Step 5: Verify Views

```sql
-- List all views
\dv

-- Expected output:
--  public | ai_decision_effectiveness | view | cdn_admin
--  public | cache_hit_ratio_by_edge   | view | cdn_admin
--  public | top_hot_content           | view | cdn_admin
```

### Step 6: Test View 1 - Cache Hit Ratio by Edge

```sql
SELECT * FROM cache_hit_ratio_by_edge;
```

**Expected**: Empty result initially (no requests yet), but structure should be:
- edge_id, region, total_requests, cache_hits, cache_misses, hit_ratio_percent, avg_response_time_ms, etc.

### Step 7: Test View 2 - Top Hot Content

```sql
SELECT * FROM top_hot_content LIMIT 5;
```

**Expected**: Empty result initially (no content/requests yet), but structure should include:
- content_id, content_type, size_kb, category, total_requests, edges_serving, hit_ratio_percent, etc.

### Step 8: Test View 3 - AI Decision Effectiveness

```sql
SELECT * FROM ai_decision_effectiveness LIMIT 5;
```

**Expected**: Empty result initially (no AI decisions yet), but structure should include:
- decision_id, decision_type, content_id, predicted_popularity, actual_requests_after_decision, prediction_accuracy_percent, etc.

### Step 9: Verify View JOINs Work

Insert test data and verify views aggregate correctly:

```sql
-- Insert test content
INSERT INTO content (content_id, content_type, size_kb, category) VALUES
    ('test-video-1', 'video', 5000, 'entertainment'),
    ('test-image-1', 'image', 200, 'news');

-- Insert test requests
INSERT INTO requests (content_id, edge_id, is_cache_hit, response_time_ms) VALUES
    ('test-video-1', 'edge-us-east', TRUE, 50),
    ('test-video-1', 'edge-us-east', FALSE, 200),
    ('test-video-1', 'edge-us-west', TRUE, 45),
    ('test-image-1', 'edge-us-east', TRUE, 30);

-- Now check views again
SELECT * FROM cache_hit_ratio_by_edge;
-- Should show aggregated stats per edge

SELECT * FROM top_hot_content;
-- Should show test-video-1 and test-image-1 with request counts
```

### Step 10: Verify Indexes

```sql
-- Check indexes on requests table
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'requests';

-- Should show indexes on content_id, edge_id, request_timestamp, is_cache_hit
```

### Step 11: Test Python DB Adapter (Optional)

If you have Python installed locally:

```bash
cd smart-cdn/backend
python -c "
from app.db.postgres import check_db_connection, get_view_cache_hit_ratio
print('Connection check:', check_db_connection())
print('View test:', get_view_cache_hit_ratio())
"
```

## Expected Schema Structure

```
edge_nodes (edge_id PK, region, cache_capacity_mb, ...)
    ↓
requests (request_id PK, content_id FK, edge_id FK, is_cache_hit, ...)
    ↓
content (content_id PK, content_type, size_kb, ...)
    ↓
ai_decisions (decision_id PK, content_id FK, edge_id FK, ...)
    ↓
experiments (experiment_id PK, ai_enabled, ...)
    ↓
metrics (metric_id PK, edge_id FK, content_id FK, ...)
    ↓
cache_state (cache_entry_id PK, edge_id FK, content_id FK, ...)
```

## Common Issues & Fixes

### Issue: "relation does not exist"
**Solution**: Schema wasn't loaded. Check:
```bash
docker-compose logs postgres
```
Look for errors during initialization. The schema.sql should be in `/docker-entrypoint-initdb.d/`.

### Issue: "permission denied"
**Solution**: Ensure you're using the correct user:
```sql
\c smart_cdn_db cdn_admin
```

### Issue: Views return no data
**Solution**: This is expected initially. Views will return data after:
- Content is inserted
- Requests are logged
- AI decisions are made

### Issue: Foreign key constraint errors
**Solution**: Insert data in order:
1. edge_nodes (already done)
2. content
3. requests (references content and edge_nodes)
4. ai_decisions (references content and edge_nodes)

## Verification Checklist

- [ ] PostgreSQL container is running
- [ ] Can connect to database
- [ ] All 7 tables exist
- [ ] All 3 views exist
- [ ] Default edge nodes inserted (3 rows)
- [ ] Default experiment inserted (1 row)
- [ ] Views execute without errors (even if empty)
- [ ] Indexes are created
- [ ] Foreign keys are working

## Next Steps

✅ **Part 2 Complete**

After verification:
- Wait for "NEXT" instruction
- Part 3 will implement edge cache simulation
- Backend will start using this database schema

---

**Status**: Database layer ready for Part 3 🚀

