# Smart CDN Load Testing with Locust

This directory contains Locust load tests for evaluating Smart CDN performance with AI-enabled vs baseline caching.

## Installation

```bash
pip install locust
```

Or add to requirements:

```bash
pip install -r requirements.txt
```

## Test Scenarios

### 1. Normal Load Test

Simulates normal user traffic with mixed content requests.

```bash
locust -f locustfile.py --host=http://localhost:8002 EdgeSimulatorUser
```

### 2. Spike Test

Simulates traffic spikes (viral content scenario).

```bash
locust -f locustfile.py --host=http://localhost:8002 SpikeTestUser --users=100 --spawn-rate=10
```

### 3. Full Stack Test

Tests the complete CDN stack including backend API.

```bash
locust -f locustfile.py --host=http://localhost:8000 CDNUser
```

## Running Tests

### Basic Usage

1. **Start Locust Web UI:**
   ```bash
   locust -f locustfile.py --host=http://localhost:8002
   ```
   
   Then open browser: `http://localhost:8089`

2. **Run from command line (headless):**
   ```bash
   locust -f locustfile.py \
     --host=http://localhost:8002 \
     --users=50 \
     --spawn-rate=5 \
     --run-time=5m \
     --headless \
     --html=report.html
   ```

### Parameters

- `--host`: Base URL for the service (edge simulator: `http://localhost:8002`, backend: `http://localhost:8000`)
- `--users`: Number of concurrent users
- `--spawn-rate`: Users spawned per second
- `--run-time`: Test duration (e.g., `5m`, `1h`)
- `--headless`: Run without web UI
- `--html`: Generate HTML report

## A/B Testing Workflow

### Step 1: Test with AI Enabled

1. **Enable AI mode:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"ai_enabled": true}'
   ```

2. **Run load test:**
   ```bash
   locust -f locustfile.py \
     --host=http://localhost:8002 \
     --users=100 \
     --spawn-rate=10 \
     --run-time=10m \
     --headless \
     --html=ai_enabled_report.html
   ```

3. **Note the experiment ID** from the response or dashboard

### Step 2: Test with AI Disabled (Baseline)

1. **Disable AI mode:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/experiments/toggle" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"ai_enabled": false}'
   ```

2. **Run load test:**
   ```bash
   locust -f locustfile.py \
     --host=http://localhost:8002 \
     --users=100 \
     --spawn-rate=10 \
     --run-time=10m \
     --headless \
     --html=baseline_report.html
   ```

3. **Note the experiment ID** from the response or dashboard

### Step 3: Compare Results

1. **Get comparison via API:**
   ```bash
   curl "http://localhost:8000/api/v1/experiments/compare?ai_experiment_id=1&baseline_experiment_id=2"
   ```

2. **View in dashboard:**
   - Navigate to `/experiments` page
   - Click "View Results" on experiments
   - Compare metrics

## Expected Metrics

### AI-Enabled Mode
- **Cache Hit Ratio**: 70-85% (higher due to AI prefetching)
- **Average Latency**: 20-40ms (lower due to better cache hits)
- **P95 Latency**: 50-80ms
- **Throughput**: Higher due to reduced origin fetches

### Baseline Mode
- **Cache Hit Ratio**: 50-65% (lower, no prefetching)
- **Average Latency**: 40-60ms (higher due to more misses)
- **P95 Latency**: 100-150ms
- **Throughput**: Lower due to more origin fetches

### Expected Improvements (AI vs Baseline)
- **Cache Hit Ratio**: +15-25% improvement
- **Average Latency**: -30-40% reduction
- **P95 Latency**: -40-50% reduction
- **Origin Fetches**: -20-30% reduction

## Spike Test Example

Simulate a viral content scenario:

```bash
locust -f locustfile.py \
  --host=http://localhost:8002 \
  --users=500 \
  --spawn-rate=50 \
  --run-time=5m \
  --headless \
  --html=spike_test_report.html \
  SpikeTestUser
```

This will:
- Generate 500 concurrent users
- Spawn 50 users per second
- Focus requests on viral content (content_id=1)
- Test system's ability to handle traffic spikes
- AI should prefetch viral content to edges

## Monitoring During Tests

1. **Watch dashboard metrics:**
   - Open `http://localhost:3000/dashboard`
   - Monitor cache hit ratio, latency, requests

2. **Check backend logs:**
   ```bash
   # If running with uvicorn
   tail -f backend.log
   ```

3. **Monitor Redis cache:**
   ```bash
   redis-cli
   > KEYS edge:*
   > TTL edge:edge-us-east-1:content:1
   ```

4. **Check database:**
   ```sql
   SELECT COUNT(*), AVG(response_time_ms), 
          SUM(CASE WHEN is_cache_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as hit_ratio
   FROM requests
   WHERE experiment_id = 1;
   ```

## Troubleshooting

### Issue: "Connection refused"
- Ensure edge simulator is running on port 8002
- Check backend is running on port 8000
- Verify services are accessible

### Issue: "Low cache hit ratio"
- Check if content is being cached
- Verify Redis is running
- Check TTL values in cache

### Issue: "High latency"
- Check origin server response time
- Verify network latency
- Check database query performance

## Advanced Usage

### Custom Test Scenarios

Create custom user classes in `locustfile.py`:

```python
class CustomTestUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def custom_scenario(self):
        # Your test logic
        pass
```

### Distributed Testing

Run Locust in distributed mode:

```bash
# Master
locust -f locustfile.py --master --host=http://localhost:8002

# Workers (on other machines)
locust -f locustfile.py --worker --master-host=MASTER_IP
```

### Export Results

```bash
locust -f locustfile.py \
  --host=http://localhost:8002 \
  --headless \
  --run-time=10m \
  --csv=results \
  --html=report.html
```

This generates:
- `results_stats.csv`: Request statistics
- `results_failures.csv`: Failed requests
- `results_exceptions.csv`: Exceptions
- `report.html`: HTML report

## Integration with CI/CD

Example GitHub Actions workflow:

```yaml
- name: Run Load Tests
  run: |
    locust -f load-test/locustfile.py \
      --host=http://localhost:8002 \
      --users=50 \
      --spawn-rate=5 \
      --run-time=5m \
      --headless \
      --html=load_test_report.html
```

## Best Practices

1. **Warm up the system** before running tests
2. **Run tests for sufficient duration** (at least 5-10 minutes)
3. **Test both AI ON and AI OFF** modes
4. **Monitor system resources** during tests
5. **Compare metrics** using the experiments API
6. **Document results** for academic evaluation
