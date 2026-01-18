# Simple Testing Guide - Experiments Endpoints (No Auth Required)

All experiments endpoints are now public (no authentication required) for easy testing.

## Quick Test Commands

### 1. Check Experiment Status

```bash
curl http://localhost:8000/api/v1/experiments/status
```

**Expected Response:**
```json
{
  "ai_enabled": true,
  "experiment": {
    "experiment_id": 1,
    "experiment_name": "AI-Enabled Mode",
    "is_active": true,
    "start_time": "2024-..."
  }
}
```

### 2. Toggle AI OFF (No Auth Required)

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
  -H "Content-Type: application/json" \
  -d '{"ai_enabled": false}'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "AI mode disabled",
  "experiment": {
    "experiment_id": 2,
    "experiment_name": "Baseline Mode",
    "ai_enabled": false,
    "start_time": "2024-..."
  }
}
```

### 3. Toggle AI ON (No Auth Required)

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
  -H "Content-Type: application/json" \
  -d '{"ai_enabled": true}'
```

### 4. Get Experiment Results

```bash
curl "http://localhost:8000/api/v1/experiments/results"
```

**Expected Response:**
```json
{
  "experiment": {
    "experiment_id": 1,
    "experiment_name": "AI-Enabled Mode",
    "ai_enabled": true
  },
  "metrics": {
    "total_requests": 100,
    "cache_hit_ratio": 75.5,
    "cache_hits": 75,
    "cache_misses": 25,
    "avg_response_time_ms": 35.2
  }
}
```

### 5. Compare Experiments

```bash
curl "http://localhost:8000/api/v1/experiments/compare?ai_experiment_id=1&baseline_experiment_id=2"
```

### 6. List All Experiments

```bash
curl "http://localhost:8000/api/v1/experiments/list"
```

## Complete A/B Test Workflow

### Step 1: Test with AI ON

```bash
# Enable AI
curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
  -H "Content-Type: application/json" \
  -d '{"ai_enabled": true}'

# Note the experiment_id from response (e.g., 1)

# Generate traffic (run Locust or make requests)
# ... generate traffic ...

# Get results
curl "http://localhost:8000/api/v1/experiments/results?experiment_id=1"
```

### Step 2: Test with AI OFF

```bash
# Disable AI
curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
  -H "Content-Type: application/json" \
  -d '{"ai_enabled": false}'

# Note the experiment_id from response (e.g., 2)

# Generate traffic
# ... generate traffic ...

# Get results
curl "http://localhost:8000/api/v1/experiments/results?experiment_id=2"
```

### Step 3: Compare Results

```bash
curl "http://localhost:8000/api/v1/experiments/compare?ai_experiment_id=1&baseline_experiment_id=2"
```

## PowerShell Examples (Windows)

### Check Status
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/experiments/status" -Method Get
```

### Toggle AI OFF
```powershell
$body = @{ai_enabled = $false} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/experiments/toggle" -Method Post -Body $body -ContentType "application/json"
```

### Toggle AI ON
```powershell
$body = @{ai_enabled = $true} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/experiments/toggle" -Method Post -Body $body -ContentType "application/json"
```

### Get Results
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/experiments/results" -Method Get
```

## Notes

- **No authentication required** - All endpoints are public for demo purposes
- **Backend must be running** - Ensure backend is running on port 8000
- **Database must be accessible** - Experiments are stored in PostgreSQL
- **Restart backend** - If you just made changes, restart the backend to load new routes

## Troubleshooting

### 404 Not Found
- Restart backend: `uvicorn app.main:app --reload`
- Check backend logs for errors

### Empty Results
- Generate some traffic first (make requests to edge simulator)
- Check if experiment_id exists in database

### Connection Refused
- Ensure backend is running on port 8000
- Check firewall settings

