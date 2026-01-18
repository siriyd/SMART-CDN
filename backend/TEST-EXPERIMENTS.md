# Testing Experiments Endpoints

Quick test guide to verify experiments endpoints are working.

## 1. Check if Backend is Running

```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

## 2. Test Experiments Status Endpoint

```bash
curl http://localhost:8000/api/v1/experiments/status
```

Expected response:
```json
{
  "ai_enabled": true,
  "experiment": {
    "experiment_id": 1,
    "experiment_name": "...",
    "is_active": true,
    "start_time": "..."
  }
}
```

If you get 404:
- Check backend logs for import errors
- Verify `routes_experiments.py` exists
- Restart backend: `uvicorn app.main:app --reload`

## 3. Test Toggle Endpoint (Requires Auth)

First, get auth token:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Then toggle:
```bash
curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ai_enabled": false}'
```

## 4. Test Results Endpoint

```bash
curl "http://localhost:8000/api/v1/experiments/results"
```

## 5. Check Backend Logs

If endpoints return 404, check for import errors:
- `ImportError: cannot import name 'experiment_service'`
- `ModuleNotFoundError: No module named 'app.services.experiment_service'`

## Common Fixes

1. **Restart Backend:**
   ```bash
   # Stop current backend
   # Then restart:
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Check Python Path:**
   ```bash
   cd backend
   python -c "from app.services.experiment_service import get_active_experiment; print('OK')"
   ```

3. **Verify File Structure:**
   ```
   backend/
   ├── app/
   │   ├── api/
   │   │   └── routes_experiments.py  ← Must exist
   │   └── services/
   │       └── experiment_service.py  ← Must exist
   ```

