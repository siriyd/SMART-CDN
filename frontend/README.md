# Smart CDN Frontend Dashboard

React-based frontend dashboard for monitoring and managing the Smart CDN system.

## Features

- **JWT Authentication**: Secure login with token-based authentication
- **Real-time Metrics**: Auto-refreshing dashboards (30s intervals)
- **Multiple Pages**:
  - Dashboard: Overview with key metrics and charts
  - AI Decisions: View and trigger AI caching decisions
  - Cache Performance: Hit/miss ratios and latency analysis
  - Edge Nodes: Monitor edge node status and capacity
  - Traffic: Request patterns and content popularity
  - Predictions: Content popularity forecasts
  - Experiments: A/B testing controls

- **Charts & Visualizations**: 
  - Recharts for interactive charts
  - Pie charts for hit/miss distribution
  - Bar charts for performance metrics
  - Line/Area charts for traffic patterns

- **Responsive Design**: Tailwind CSS for mobile-friendly UI

## Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8000
- AI Engine running on port 8001

## Installation

```bash
cd smart-cdn/frontend
npm install
```

## Configuration

Create `.env` or `.env.local` file (optional, defaults work for local dev):

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_AI_ENGINE_URL=http://localhost:8001
```

## Running the Frontend

### Development Mode

```bash
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Production Build

```bash
npm run build
npm run preview
```

## Default Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js          # Axios-based API client
│   ├── components/
│   │   ├── Navbar.jsx         # Navigation bar
│   │   ├── MetricCard.jsx    # Metric display card
│   │   ├── HitMissChart.jsx   # Cache hit/miss pie chart
│   │   ├── TrafficChart.jsx   # Traffic line chart
│   │   ├── EdgeMap.jsx        # Edge node visualization
│   │   └── ExperimentToggle.jsx # AI toggle switch
│   ├── pages/
│   │   ├── Login.jsx          # Login page
│   │   ├── Dashboard.jsx     # Main dashboard
│   │   ├── AIDecisions.jsx   # AI decisions page
│   │   ├── CachePerformance.jsx # Cache metrics
│   │   ├── EdgeNodes.jsx     # Edge monitoring
│   │   ├── Traffic.jsx       # Traffic patterns
│   │   ├── Predictions.jsx   # Popularity predictions
│   │   └── Experiments.jsx   # A/B testing
│   ├── App.jsx               # Main router
│   ├── main.jsx              # React entry point
│   └── styles.css            # Tailwind CSS
├── package.json
├── vite.config.js
├── tailwind.config.js
└── index.html
```

## API Integration

The frontend communicates with the backend via REST API:

- **Authentication**: `/api/v1/auth/*`
- **Metrics**: `/api/v1/metrics/*`
- **AI Decisions**: `/api/v1/ai/*`
- **Edges**: `/api/v1/edges/*`
- **Requests**: `/api/v1/requests`
- **Content**: `/api/v1/content`

All API calls are handled by `src/api/client.js` with automatic token injection and error handling.

## Technologies Used

- **React 18**: UI framework
- **React Router 6**: Client-side routing
- **Recharts**: Chart library
- **Axios**: HTTP client
- **Tailwind CSS**: Styling
- **Vite**: Build tool

## Troubleshooting

### CORS Errors
If you see CORS errors, ensure the backend allows requests from `http://localhost:3000`.

### 401 Unauthorized
- Token may have expired
- Logout and login again
- Check backend auth endpoint is working

### Charts Not Rendering
- Check browser console for errors
- Verify data format matches expected schema
- Ensure Recharts is installed: `npm install recharts`

### API Connection Failed
- Verify backend is running on port 8000
- Check `VITE_API_BASE_URL` in `.env`
- Test backend health: `curl http://localhost:8000/health`

## Development Notes

- Auto-refresh interval: 30 seconds
- Token stored in `localStorage` as `auth_token`
- Protected routes require authentication
- All API errors are logged to console

## Next Steps

See `PART6-VERIFICATION.md` for detailed verification steps.

