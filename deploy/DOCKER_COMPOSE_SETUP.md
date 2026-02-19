# Docker Compose Development Setup

## Quick Start

```bash
# 1. Start all services
make docker-up

# 2. Access services
# - Frontend: http://localhost:4200
# - Backend:  http://localhost:8000
# - Database: postgresql://localhost:5432
# - Adminer:  http://localhost:8080 (Database UI)

# 3. View logs
make docker-logs

# 4. Stop services
make docker-down
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Docker Compose Network                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐  ┌──────────────┐                 │
│  │  Frontend   │  │  Backend     │                 │
│  │  :4200      │  │  :8000       │                 │
│  └─────┬───────┘  └──────┬───────┘                 │
│        │                 │                          │
│        └─────────┬───────┘                          │
│                  │                                  │
│            ┌─────▼────────┐                         │
│            │              │                         │
│        ┌───▼─────────────────┐                      │
│        │  PostgreSQL         │                      │
│        │  Database :5432     │                      │
│        └─────────────────────┘                      │          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Services

### PostgreSQL Database (db)

- **Image**: postgres:16-alpine
- **Port**: 5432
- **Credentials**: 
  - User: `postgres`
  - Password: `postgres` (from .env)
  - Database: `myproject_dev`
- **Volume**: `postgres_data:/var/lib/postgresql/data`
- **Health Check**: PostgreSQL readiness check every 10s

### FastAPI Backend (backend)

- **Port**: 8000
- **Build**: `../backend/Dockerfile`
- **Environment**: All variables from `.env` file
- **Volumes**: 
  - `../backend:/app` - Source code (hot-reload)
  - `/app/__pycache__` - Excluded from mount
- **Depends On**: `db` (healthy)
- **Health Check**: GET `/health` endpoint
- **Debug**: Auto-reload enabled when `BACKEND_RELOAD=true`

### Angular Frontend (frontend)

- **Port**: 4200
- **Build**: `../frontend/Dockerfile`
- **Environment**: API_BASE_URL, FRONTEND_URL from `.env`
- **Volumes**: 
  - `../frontend:/app` - Source code
  - `/app/node_modules` - Excluded from mount
- **Depends On**: `backend` service

### Adminer (Database Management UI)

- **Image**: adminer:latest
- **Port**: 8080
- **Purpose**: Web-based database administration
- **Access**: http://localhost:8080
- **Credentials**: Same as PostgreSQL service

## Environment Configuration

### Using .env File

```bash
# 1. Create .env from template
cp .env.local.example .env

# 2. Edit if needed (usually defaults are fine for local)
nano .env

# 3. Docker Compose automatically loads .env
make docker-up
```

### Common .env Variables

```bash
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=myproject_dev

# API
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:4200

# Secrets (safe for dev only!)
JWT_SECRET_KEY=dev-secret-key

# Logging
LOG_FORMAT=text
LOG_OUTPUT=console
```

## Common Commands

### Starting & Stopping

```bash
# Start all services in background
make docker-up

# Stop all services
make docker-down

# Restart all services
make docker-restart

# View running containers
make docker-ps
```

### Viewing Logs

```bash
# All services
make docker-logs

# Specific service
make docker-logs-backend
make docker-logs-frontend
make docker-logs-db

# Follow logs in real-time
docker-compose -f deploy/docker-compose.yml logs -f backend

# View last N lines
docker-compose -f deploy/docker-compose.yml logs --tail=100 backend
```

### Accessing Services

```bash
# SSH into backend container
docker-compose -f deploy/docker-compose.yml exec backend bash

# SSH into database
docker-compose -f deploy/docker-compose.yml exec db psql -U postgres
```

### Database Management

```bash
# Connect to database
psql postgresql://postgres:postgres@localhost:5432/myproject_dev

# View databases
\l

# Connect to database
\c myproject_dev

# List tables
\dt

# Exit psql
\q

# Or use Adminer UI at http://localhost:8080
```

### Running Tests Inside Docker

```bash
# Backend tests
docker-compose -f deploy/docker-compose.yml exec backend \
  pytest tests/ -v --tb=short

# Integration tests
docker-compose -f deploy/docker-compose.yml exec backend \
  pytest tests/integration -v

# E2E tests
docker-compose -f deploy/docker-compose.yml exec backend \
  pytest tests/e2e -v
```

## Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in .env
# Set BACKEND_PORT=8001 and rebuild
```

### Database Connection Failed

```bash
# Check if db service is running
docker-compose -f deploy/docker-compose.yml ps

# Check database logs
make docker-logs-db

# Restart database
docker-compose -f deploy/docker-compose.yml restart db

# Verify database is healthy
docker-compose -f deploy/docker-compose.yml exec db pg_isready
```

### Backend Won't Start

```bash
# 1. Check logs
make docker-logs-backend

# 2. Verify environment variables
docker-compose -f deploy/docker-compose.yml config | grep DATABASE

# 3. Wait for db to be healthy
docker-compose -f deploy/docker-compose.yml exec db pg_isready

# 4. Rebuild backend image
docker-compose -f deploy/docker-compose.yml build --no-cache backend
```

### Frontend Won't Load

```bash
# Check frontend logs
make docker-logs-frontend

# Check if Angular dev server is running
curl http://localhost:4200

# Restart frontend service
docker-compose -f deploy/docker-compose.yml restart frontend

# Full rebuild
docker-compose -f deploy/docker-compose.yml build --no-cache frontend
```

## Cleaning Up

### Remove Stopped Containers

```bash
docker container prune
```

### Remove Unused Volumes

```bash
docker volume prune
```

### Full Cleanup (WARNING: Removes all data!)

```bash
# Stop and remove all containers, networks, volumes
make docker-clean

# Or manually:
docker-compose -f deploy/docker-compose.yml down -v
```

## Advanced Usage

### Rebuild Specific Service

```bash
# Rebuild backend with no cache
docker-compose -f deploy/docker-compose.yml build --no-cache backend

# Start with new build
docker-compose -f deploy/docker-compose.yml up backend
```

### Scale Services

```bash
# Run 3 backend instances (with load balancing)
# Note: Need to remove port binding first
docker-compose -f deploy/docker-compose.yml up --scale backend=3
```

### Custom Environment Override

```bash
# Set custom value for single command
BACKEND_PORT=9000 docker-compose -f deploy/docker-compose.yml up backend
```

### Attach to Service

```bash
# See real-time logs from backend
docker attach myproject_backend
```

## Performance Tips

### 1. Use Volume Excludes

The `docker-compose.yml` already excludes:
- `/app/__pycache__`
- `/app/node_modules`

This prevents syncing Python/Node caches, improving performance.

### 2. Increase Docker Resources

If Docker is slow:
- Mac/Windows: Docker Desktop → Preferences → Resources → Increase CPUs/RAM
- Linux: Docker runs native, check system resources

### 3. Use .dockerignore

Frontend and backend both have `.dockerignore` files to exclude unnecessary files from Docker context.

### 4. Enable BuildKit

```bash
export DOCKER_BUILDKIT=1
docker-compose -f deploy/docker-compose.yml build
```

## Production Differences

This docker-compose setup is **development-focused**:

| Feature | Development | Production |
|---------|-------------|-----------|
| Debug Mode | ✅ Enabled | ❌ Disabled |
| Hot Reload | ✅ Enabled | ❌ No reload |
| Logging | Text (console) | JSON (structured) |
| Health Checks | ✅ Yes | ✅ Yes |
| Volumes | Mounted (code sync) | ❌ No volumes |
| Adminer UI | ✅ Included | ❌ Removed |
| Workers | 1 | 4-8 |
| Resources | Limited | High |

For production, use:
- ECS (AWS container orchestration)
- RDS (managed database)
- See [infra/README.md](../infra/README.md) for production setup

## See Also

- [Makefile](../Makefile) - All make targets
- [ENV_MANAGEMENT.md](../ENV_MANAGEMENT.md) - Environment variable guide
- [backend/README.md](../backend/README.md) - Backend setup
- [frontend/README.md](../frontend/README.md) - Frontend setup
