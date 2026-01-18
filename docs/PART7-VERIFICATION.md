# Part 7 - Experiment Mode (AI ON/OFF) + Evaluation Verification Guide

## Overview
Part 7 implements A/B testing capabilities to compare AI-enabled caching against baseline LRU/LFU caching, with load testing support using Locust.

## Prerequisites
- Backend running on port 8000
- Edge Simulator running on port 8002
- PostgreSQL and Redis running
- Locust installed: `pip install locust`

## Step 1: Verify Experiment Service

1. **Check experiment status:**
   ```bash
   curl http://localhost:8000/api/v1/experiments/status
   ```

   Expected response:
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

2. **Verify default experiment exists:**
   - If no experiment exists, the system defaults to AI enabled
   - First toggle will create an experiment

## Step 2: Test AI Toggle (Backend)

1. **Toggle AI OFF:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"ai_enabled": false}'
   ```

   Expected response:
   ```json
   {
     "status": "success",
     "message": "AI mode disabled",
     "experiment": {
       "experiment_id": 2,
       "experiment_name": "Baseline Mode",
       "ai_enabled": false
     }
   }
   ```

2. **Verify AI decisions are blocked:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ai/decide?time_window_minutes=60"
   ```

   Expected response:
   ```json
   {
     "status": "skipped",
     "message": "AI is currently disabled. Enable AI mode to generate decisions."
   }
   ```

3. **Toggle AI ON:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"ai_enabled": true}'
   ```

4. **Verify AI decisions work:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ai/decide?time_window_minutes=60"
   ```

   Should return AI decisions (not skipped).

## Step 3: Test Frontend Toggle

1. **Login to dashboard:**
   - Navigate to `http://localhost:3000`
   - Login with `admin` / `admin123`

2. **Go to Experiments page:**
   - Click "Experiments" in navbar
   - URL: `http://localhost:3000/experiments`

3. **Test toggle:**
   - Toggle switch should show current AI status
   - Click toggle to switch modes
   - Should see success message
   - Status should update immediately

4. **Verify experiment list:**
   - Should see list of recent experiments
   - Each experiment shows: Name, AI Enabled status, Start Time, Status

## Step 4: Test Request Logging with Experiments

1. **Generate some traffic:**
   ```bash
   # Request content through edge simulator
   curl http://localhost:8002/edge/edge-us-east-1/content/1
   ```

2. **Check request was logged with experiment_id:**
   ```bash
   curl "http://localhost:8000/api/v1/requests?limit=10"
   ```

   Verify `experiment_id` is set in request logs.

3. **Toggle experiment and generate more traffic:**
   - Toggle AI mode
   - Generate more requests
   - Verify new requests have new `experiment_id`

## Step 5: Test Experiment Results

1. **Get current experiment results:**
   ```bash
   curl "http://localhost:8000/api/v1/experiments/results"
   ```

   Expected response:
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
       "avg_response_time_ms": 35.2,
       "avg_hit_latency_ms": 20.1,
       "avg_miss_latency_ms": 80.5
     }
   }
   ```

2. **Get specific experiment results:**
   ```bash
   curl "http://localhost:8000/api/v1/experiments/results?experiment_id=1"
   ```

## Step 6: Test Experiment Comparison

1. **Run test with AI ON:**
   - Toggle AI ON
   - Generate traffic (or run Locust test)
   - Note experiment_id (e.g., 1)

2. **Run test with AI OFF:**
   - Toggle AI OFF
   - Generate traffic (or run Locust test)
   - Note experiment_id (e.g., 2)

3. **Compare experiments:**
   ```bash
   curl "http://localhost:8000/api/v1/experiments/compare?ai_experiment_id=1&baseline_experiment_id=2"
   ```

   Expected response:
   ```json
   {
     "ai_experiment": {...},
     "baseline_experiment": {...},
     "ai_metrics": {
       "cache_hit_ratio": 80.5,
       "avg_response_time_ms": 30.2
     },
     "baseline_metrics": {
       "cache_hit_ratio": 65.3,
       "avg_response_time_ms": 45.8
     },
     "improvements": {
       "cache_hit_ratio_improvement_pct": 23.3,
       "latency_improvement_pct": 34.1,
       "latency_reduction_ms": 15.6
     }
   }
   ```

## Step 7: Install and Run Locust Tests

1. **Install Locust:**
   ```bash
   pip install locust
   ```

2. **Start Locust Web UI:**
   ```bash
   cd smart-cdn/load-test
   locust -f locustfile.py --host=http://localhost:8002
   ```

3. **Open Locust UI:**
   - Navigate to `http://localhost:8089`
   - Set users: 50
   - Set spawn rate: 5
   - Click "Start Swarming"

4. **Monitor results:**
   - Watch request statistics
   - Check response times
   - Monitor failures

## Step 8: Run Spike Test

1. **Run spike test (headless):**
   ```bash
   locust -f locustfile.py \
     --host=http://localhost:8002 \
     --users=100 \
     --spawn-rate=20 \
     --run-time=5m \
     --headless \
     --html=spike_test_report.html \
     SpikeTestUser
   ```

2. **Check report:**
   - Open `spike_test_report.html`
   - Review metrics
   - Check for errors

## Step 9: Full A/B Test Workflow

1. **Test with AI ON:**
   ```bash
   # Enable AI
   curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"ai_enabled": true}'
   
   # Run load test
   locust -f load-test/locustfile.py \
     --host=http://localhost:8002 \
     --users=100 \
     --spawn-rate=10 \
     --run-time=10m \
     --headless \
     --html=ai_enabled_report.html
   
   # Note experiment_id from dashboard or API
   ```

2. **Test with AI OFF:**
   ```bash
   # Disable AI
   curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"ai_enabled": false}'
   
   # Run load test
   locust -f load-test/locustfile.py \
     --host=http://localhost:8002 \
     --users=100 \
     --spawn-rate=10 \
     --run-time=10m \
     --headless \
     --html=baseline_report.html
   
   # Note experiment_id from dashboard or API
   ```

3. **Compare results:**
   ```bash
   curl "http://localhost:8000/api/v1/experiments/compare?ai_experiment_id=1&baseline_experiment_id=2"
   ```

4. **View in dashboard:**
   - Go to Experiments page
   - View comparison results
   - Check improvement percentages

## Step 10: Verify Baseline Caching

1. **With AI OFF, verify baseline caching works:**
   - Toggle AI OFF
   - Request content multiple times
   - Check cache hit ratio improves over time
   - Verify LRU/LFU eviction works

2. **Check Redis cache:**
   ```bash
   redis-cli
   > KEYS edge:*
   > TTL edge:edge-us-east-1:content:1
   ```

## Expected Results

### AI-Enabled Mode
- **Cache Hit Ratio**: 70-85%
- **Average Latency**: 20-40ms
- **P95 Latency**: 50-80ms
- **AI Decisions**: Generated and applied

### Baseline Mode
- **Cache Hit Ratio**: 50-65%
- **Average Latency**: 40-60ms
- **P95 Latency**: 100-150ms
- **AI Decisions**: Blocked/skipped

### Improvements (AI vs Baseline)
- **Cache Hit Ratio**: +15-25% improvement
- **Average Latency**: -30-40% reduction
- **P95 Latency**: -40-50% reduction

## Common Issues & Fixes

### Issue 1: "No experiment found"
- **Fix**: Toggle AI mode once to create initial experiment

### Issue 2: "AI decisions still generated when AI is OFF"
- **Fix**: Check `is_ai_enabled()` check in `routes_ai.py`

### Issue 3: "Requests not assigned experiment_id"
- **Fix**: Verify `get_active_experiment()` in `routes_requests.py`

### Issue 4: "Locust connection refused"
- **Fix**: Ensure edge simulator is running on port 8002

### Issue 5: "Comparison shows no improvement"
- **Fix**: Ensure sufficient traffic was generated for both experiments

## Success Criteria

✅ Toggle AI ON/OFF works from API and frontend  
✅ AI decisions blocked when AI is OFF  
✅ Requests automatically assigned experiment_id  
✅ Experiment results endpoint returns metrics  
✅ Comparison endpoint shows improvements  
✅ Locust tests run successfully  
✅ Spike test handles traffic spikes  
✅ Baseline caching works with LRU/LFU  
✅ Frontend Experiments page displays results  

## Next Steps

After Part 7 verification:
- A/B testing infrastructure is complete
- Load testing capabilities are ready
- Metrics comparison is functional
- Ready for academic evaluation and demonstration

**Part 7 is complete!** 🎉

