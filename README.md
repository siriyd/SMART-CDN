# Smart CDN with AI-Driven Caching

A complete distributed CDN system with AI-powered caching intelligence, demonstrating edge caching, cache hit/miss behavior, predictive prefetching, and dynamic TTL management.

## Architecture Overview

- **Backend API**: FastAPI service managing content, metrics, and cache decisions
- **AI Engine**: Microservice providing popularity predictions and caching policies
- **Edge Simulator**: Simulates multiple edge nodes with Redis caching
- **Frontend Dashboard**: React dashboard for monitoring and visualization
- **PostgreSQL**: Structured data storage (requests, metrics, experiments)
- **Redis**: Edge cache layer with TTL management

## Part 1: Project Bootstrap & Docker Setup

### Prerequisites

- Docker Desktop (or Docker + Docker Compose)
- Git
- Terminal/Command Prompt

### Quick Start

1. **Clone/Navigate to project directory**
   ```bash
   cd smart-cdn
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```
   (Optional: Edit `.env` if you want to change defaults)

3. **Build and start all services**
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build all Docker images
   - Start PostgreSQL, Redis, Backend, AI Engine, Edge Simulator, and Frontend
   - Wait for health checks before starting dependent services

4. **Verify services are running**

   Open separate terminals and check:

   ```bash
   # Backend API
   curl http://localhost:8000/health
   # Expected: {"status":"healthy","service":"backend","version":"1.0.0"}

   # AI Engine
   curl http://localhost:8001/health
   # Expected: {"status":"healthy","service":"ai-engine","version":"1.0.0"}

   # Edge Simulator
   curl http://localhost:8002/health
   # Expected: {"status":"healthy","service":"edge-sim","version":"1.0.0"}
   ```

   Or check Docker containers:
   ```bash
   docker-compose ps
   ```

   All services should show "Up" status.

5. **Access Frontend**
   - Open browser: http://localhost:3000
   - You should see "Smart CDN Dashboard" placeholder

### Service Ports

| Service | Port | URL |
|---------|------|-----|
| Backend API | 8000 | http://localhost:8000 |
| AI Engine | 8001 | http://localhost:8001 |
| Edge Simulator | 8002 | http://localhost:8002 |
| Frontend | 3000 | http://localhost:3000 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

### Common Issues & Fixes

**Issue: Port already in use**
- Solution: Stop other services using ports 3000, 8000, 8001, 8002, 5432, 6379
- Or modify ports in `docker-compose.yml` and `.env`

**Issue: Docker build fails**
- Solution: Ensure Docker Desktop is running
- Check: `docker --version` and `docker-compose --version`

**Issue: Services won't start**
- Solution: Check logs: `docker-compose logs [service-name]`
- Example: `docker-compose logs backend`

**Issue: Database connection errors**
- Solution: Wait 10-15 seconds after `docker-compose up` for PostgreSQL to initialize
- Check: `docker-compose logs postgres`

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

### Next Steps

After verifying Part 1 works:
- Wait for "NEXT" instruction
- Part 2 will add PostgreSQL schema and views

---

**Status**: Part 1 Complete ✅


