# Part 6 - Frontend Dashboard Verification Guide

## Overview
Part 6 implements a complete React frontend dashboard with authentication, real-time metrics, charts, and multiple pages for monitoring the Smart CDN system.

## Prerequisites
- Backend running on port 8000
- AI Engine running on port 8001
- Edge Simulator running on port 8002
- PostgreSQL and Redis running
- Node.js 18+ and npm installed

## Step 1: Install Frontend Dependencies

```bash
cd smart-cdn/frontend
npm install
```

Expected output:
- All dependencies installed successfully
- `node_modules` directory created
- No errors

## Step 2: Configure Environment Variables

Ensure `.env` or `.env.local` exists in `frontend/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_AI_ENGINE_URL=http://localhost:8001
```

Or use the default values (already configured in `vite.config.js`).

## Step 3: Start Frontend Development Server

```bash
npm run dev
```

Expected output:
```
  VITE v5.0.5  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

## Step 4: Verify Login Page

1. Open browser: `http://localhost:3000`
2. You should be redirected to `/login`
3. Login page should display:
   - "Smart CDN Dashboard" title
   - Username and password fields
   - "Sign In" button
   - Default credentials hint: `admin / admin123`

**Test Login:**
- Username: `admin`
- Password: `admin123`
- Click "Sign In"

Expected result:
- Redirected to `/dashboard`
- Navbar appears at top
- Dashboard content loads

## Step 5: Verify Dashboard Page

After login, you should see:

### Navigation Bar
- "Smart CDN Dashboard" logo (left)
- Navigation links: Dashboard, AI Decisions, Cache Performance, Edge Nodes, Traffic
- Welcome message with username
- Logout button (right)

### Dashboard Content
- **Key Metrics Cards** (4 cards):
  - Total Requests
  - Cache Hit Ratio (%)
  - Avg Latency (ms)
  - Active Edges

- **Charts**:
  - Cache Hit/Miss by Edge (Pie chart)
  - Request Distribution (Line chart)

- **Top Popular Content Table**:
  - Columns: Content ID, Type, Requests, Hit Ratio, Avg Latency
  - Shows top 10 popular content items

- **"Trigger AI Decisions" Button** (top right):
  - Click to trigger AI decision generation
  - Should show success message

## Step 6: Verify AI Decisions Page

1. Click "AI Decisions" in navbar
2. URL: `http://localhost:3000/ai-decisions`

Expected content:
- **Summary Cards** (3 cards):
  - Prefetch Decisions count
  - Eviction Decisions count
  - TTL Updates count

- **"Trigger AI Decisions" Button**:
  - Click to generate new decisions
  - Should show success message with count

- **Recent Decisions Table**:
  - Columns: Decision ID, Type, Content ID, Edge ID, Priority, Timestamp, Applied
  - Shows recent AI decisions
  - Color-coded decision types (prefetch=green, evict=red, ttl_update=blue)

**Test:**
- Click "Trigger AI Decisions"
- Wait for success message
- Verify table updates with new decisions

## Step 7: Verify Cache Performance Page

1. Click "Cache Performance" in navbar
2. URL: `http://localhost:3000/cache-performance`

Expected content:
- **Summary Cards** (4 cards):
  - Overall Hit Ratio (%)
  - Total Hits
  - Total Misses
  - Latency Improvement (ms)

- **Charts**:
  - Cache Hit/Miss by Edge (Pie chart)
  - Hit Ratio by Edge (Bar chart)
  - Latency Comparison: Hit vs Miss (Bar chart)

- **Edge Performance Table**:
  - Columns: Edge ID, Region, Hit Ratio, Total Requests, Hits, Misses, Avg Latency
  - Color-coded hit ratios (green >70%, yellow >50%, red <50%)

## Step 8: Verify Edge Nodes Page

1. Click "Edge Nodes" in navbar
2. URL: `http://localhost:3000/edge-nodes`

Expected content:
- **Summary Cards** (4 cards):
  - Total Edges
  - Active Edges
  - Total Capacity (MB)
  - Total Usage (MB)

- **Edge Map**:
  - Grid of edge node cards
  - Each card shows: Edge ID, Region, Status, Capacity, Usage, Utilization bar
  - Clickable cards (click to view stats)

- **Selected Edge Stats** (appears after clicking an edge):
  - Cache Hit Ratio details
  - Latency Metrics

- **All Edge Nodes Table**:
  - Columns: Edge ID, Region, Capacity, Usage, Utilization, Status
  - Clickable rows to view stats

## Step 9: Verify Traffic Page

1. Click "Traffic" in navbar
2. URL: `http://localhost:3000/traffic`

Expected content:
- **Request Traffic Chart** (Last Hour):
  - Area chart showing requests, hits, misses over time
  - Grouped by 5-minute intervals

- **Content Popularity Chart**:
  - Bar chart showing top 10 content by requests
  - Multiple bars: Total Requests, Last Hour, Last 24h

- **Recent Requests Table**:
  - Columns: Timestamp, Content ID, Edge ID, Cache Status (HIT/MISS), Response Time
  - Shows last 50 requests
  - Color-coded cache status

## Step 10: Verify Predictions Page

1. Click "Predictions" in navbar (if available) or navigate to `/predictions`
2. URL: `http://localhost:3000/predictions`

Expected content:
- **Top Popular Content Chart**:
  - Bar chart with Total Requests, Last Hour, Last 24h

- **Popularity Rankings Table**:
  - Columns: Rank, Content ID, Type, Total Requests, Last Hour, Last 24h, Hit Ratio, Edges Serving
  - Sorted by popularity

## Step 11: Verify Experiments Page

1. Navigate to `/experiments`
2. URL: `http://localhost:3000/experiments`

Expected content:
- **AI Engine Status Toggle**:
  - Toggle switch to enable/disable AI
  - Shows current status

- **A/B Testing Section**:
  - AI-Enabled Mode description
  - Baseline Mode description

- **Metrics Comparison**:
  - Placeholder for experiment results

## Step 12: Verify Authentication & Logout

1. Click "Logout" button in navbar
2. Expected result:
   - Redirected to `/login`
   - Token removed from localStorage
   - Navbar disappears

3. Try accessing protected route directly:
   - Navigate to `http://localhost:3000/dashboard`
   - Should redirect to `/login`

4. Login again and verify access restored

## Step 13: Verify Real-time Updates

1. On Dashboard page, wait 30 seconds
2. Metrics should auto-refresh (check browser console for API calls)
3. All pages have 30-second auto-refresh intervals

## Step 14: Verify Responsive Design

1. Resize browser window to mobile size (< 768px)
2. Verify:
   - Navigation collapses appropriately
   - Charts remain readable
   - Tables scroll horizontally
   - Cards stack vertically

## Step 15: Verify Error Handling

1. Stop backend server
2. Refresh dashboard
3. Expected:
   - Error message displayed
   - Loading states handled gracefully
   - No crashes

4. Restart backend
5. Refresh page
6. Expected: Data loads successfully

## Common Issues & Fixes

### Issue 1: "Failed to load metrics"
- **Cause**: Backend not running or wrong API URL
- **Fix**: Verify backend on port 8000, check `VITE_API_BASE_URL` in `.env`

### Issue 2: "401 Unauthorized" errors
- **Cause**: Token expired or invalid
- **Fix**: Logout and login again

### Issue 3: Charts not rendering
- **Cause**: Recharts not installed or data format incorrect
- **Fix**: Run `npm install`, check browser console for errors

### Issue 4: CORS errors
- **Cause**: Backend not allowing frontend origin
- **Fix**: Add CORS middleware to backend (if needed)

### Issue 5: Login fails
- **Cause**: Backend auth endpoint not working
- **Fix**: Verify `routes_auth.py` is included in `main.py`, check backend logs

## Expected File Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js          # API client with axios
│   ├── components/
│   │   ├── Navbar.jsx
│   │   ├── MetricCard.jsx
│   │   ├── HitMissChart.jsx
│   │   ├── TrafficChart.jsx
│   │   ├── EdgeMap.jsx
│   │   └── ExperimentToggle.jsx
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   ├── AIDecisions.jsx
│   │   ├── CachePerformance.jsx
│   │   ├── EdgeNodes.jsx
│   │   ├── Traffic.jsx
│   │   ├── Predictions.jsx
│   │   └── Experiments.jsx
│   ├── App.jsx                # Main router
│   ├── main.jsx               # React entry point
│   └── styles.css             # Tailwind CSS
├── package.json
├── vite.config.js
├── tailwind.config.js
└── index.html
```

## Success Criteria

✅ Login page works with default credentials  
✅ All dashboard pages load without errors  
✅ Charts render with real data  
✅ Real-time updates work (30s intervals)  
✅ Navigation between pages works  
✅ Logout redirects to login  
✅ Protected routes require authentication  
✅ Responsive design works on mobile  
✅ Error handling displays user-friendly messages  

## Next Steps

After Part 6 verification:
- All frontend pages are functional
- Dashboard displays real-time metrics
- AI decisions can be triggered from UI
- Cache performance is visualized
- Edge nodes are monitored
- Traffic patterns are tracked

**Part 6 is complete!** 🎉

