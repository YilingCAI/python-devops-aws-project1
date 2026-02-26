# Backend

FastAPI application with PostgreSQL, JWT authentication, SQLAlchemy ORM, and Alembic migrations.

---

## Table of Contents

1. [Local Setup](#local-setup)
2. [Project Structure](#project-structure)
3. [Configuration](#configuration)
4. [Database Migrations](#database-migrations)
5. [API Reference](#api-reference)
6. [Running Tests](#running-tests)
7. [Docker](#docker)

---

## Local Setup

### Requirements

- Python 3.12+
- Poetry 1.8+
- PostgreSQL 16 (or run via Docker Compose — recommended)

### Install dependencies

```bash
cd backend
poetry install
```

### Start with Docker Compose (recommended)

From the project root:

```bash
cp config/.env.dev deploy/.env
docker compose -f deploy/docker-compose.yml up postgres backend --build
```

- API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Start manually (if you have a local Postgres)

```bash
cd backend

# Copy and configure environment
cp ../config/.env.dev .env.local
# Edit .env.local — set DATABASE_HOST=localhost

# Activate the poetry shell
poetry shell

# Apply migrations
alembic upgrade head

# Start dev server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Project Structure

```
backend/
├── main.py                  ← ASGI entry point (imports app from app/main.py)
├── pyproject.toml           ← Python dependencies (Poetry)
├── pytest.ini               ← pytest markers and options
├── alembic.ini              ← Alembic migration config
│
├── app/
│   ├── main.py              ← FastAPI app instance, lifespan, middleware
│   │
│   ├── api/                 ← Route handlers (thin — validate, delegate to service, return)
│   │   ├── health.py        ← GET /health
│   │   ├── user.py          ← POST /users, GET /users/me, etc.
│   │   └── game.py          ← GET/POST/PUT/DELETE /games
│   │
│   ├── core/
│   │   ├── config.py        ← pydantic-settings; reads env vars, validates at startup
│   │   ├── security.py      ← JWT create/verify, bcrypt/argon2 password hashing
│   │   └── logging.py       ← JSON structured logger
│   │
│   ├── db/
│   │   ├── base.py          ← SQLAlchemy declarative base
│   │   └── session.py       ← async engine + session factory, get_db() dependency
│   │
│   ├── models/              ← SQLAlchemy ORM models (maps to DB tables)
│   │   ├── user.py
│   │   └── game.py
│   │
│   ├── schemas/             ← Pydantic models (API contract — request/response shapes)
│   │   ├── user.py
│   │   └── game.py
│   │
│   └── services/            ← Business logic (no HTTP context, no direct DB calls)
│       ├── user_service.py
│       └── game_service.py
│
├── alembic/
│   ├── env.py               ← Alembic environment configuration
│   ├── script.py.mako       ← Migration file template
│   └── versions/            ← Auto-generated migration scripts
│
└── tests/
    ├── conftest.py           ← Shared fixtures (DB engine, session, client, auth)
    ├── unit/                 ← Fully mocked tests — no DB, no network
    │   ├── services/
    │   └── core/
    └── integration/          ← Real DB tests — auto-rollback per test
        ├── api/
        └── db/
```

---

## Configuration

All configuration is read by `app/core/config.py` using `pydantic-settings`. It reads variables from the environment (or a `.env` file in development).

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` / `test` / `staging` / `production` |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_HOST` | `localhost` | Postgres host |
| `DATABASE_PORT` | `5432` | Postgres port |
| `DATABASE_NAME` | — | Database name |
| `DATABASE_USER` | — | Database user |
| `DATABASE_PASSWORD` | — | **Secret — never in config files** |
| `JWT_SECRET_KEY` | — | **Secret — never in config files** |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

In production, `DATABASE_PASSWORD` and `JWT_SECRET_KEY` are fetched from **AWS Secrets Manager** at container startup, not from environment files.

For local development, use `config/.env.dev` (already has safe test values for all required variables).

---

## Database Migrations

Migrations are managed by Alembic and stored in `alembic/versions/`.

```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Check current migration state
poetry run alembic current

# Generate a new migration after changing a model
poetry run alembic revision --autogenerate -m "add score column to games"

# Roll back one migration
poetry run alembic downgrade -1

# Roll back to a specific revision
poetry run alembic downgrade abc123

# Show migration history
poetry run alembic history --verbose
```

### Migration workflow

1. Edit a model in `app/models/`
2. Run `alembic revision --autogenerate -m "description"` to generate the script
3. Review the generated file in `alembic/versions/` — never trust autogenerate blindly
4. Run `alembic upgrade head` to apply
5. Commit both the model change and the migration file together

---

## API Reference

The full interactive API docs are available at http://localhost:8000/docs when running locally.

### Health

```
GET /health
→ 200 {"status": "ok", "environment": "development"}
```

### Authentication

```
POST /auth/register
Body: {"email": "user@example.com", "password": "StrongPass1!"}
→ 201 {"id": 1, "email": "user@example.com"}

POST /auth/login
Body: {"email": "user@example.com", "password": "StrongPass1!"}
→ 200 {"access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer"}

POST /auth/refresh
Header: Authorization: Bearer <refresh_token>
→ 200 {"access_token": "eyJ...", "token_type": "bearer"}

POST /auth/logout
Header: Authorization: Bearer <access_token>
→ 204
```

### Users

```
GET /users/me
Header: Authorization: Bearer <access_token>
→ 200 {"id": 1, "email": "user@example.com", "created_at": "..."}
```

### Games

```
GET    /games           ← list all games for authenticated user
POST   /games           ← create a new game
GET    /games/{id}      ← get a specific game
PUT    /games/{id}      ← update a game
DELETE /games/{id}      ← delete a game
```

---

## Running Tests

```bash
cd backend

# All tests
poetry run pytest

# Unit tests only (fast, no DB)
poetry run pytest tests/unit -m unit -v

# Integration tests only (requires postgres — start via docker compose)
poetry run pytest tests/integration -m integration -v

# With coverage
poetry run pytest --cov=app --cov-report=html --cov-report=term
open htmlcov/index.html

# Specific test
poetry run pytest tests/unit/services/test_user_service.py::TestUserRegistration::test_register_success -v

# Watch mode (re-run on file changes)
poetry run pytest-watch
```

### Test markers

| Marker | Description |
|---|---|
| `@pytest.mark.unit` | No DB, no network — runs in < 1s per test |
| `@pytest.mark.integration` | Real DB with automatic rollback after each test |

Unit tests mock all external dependencies. Integration tests use a real postgres container with transaction rollback per test — the DB is never dirty between tests.

---

## Docker

```bash
# Build image
docker build -t myproject-backend:local ./backend

# Run container (requires postgres)
docker run --rm \
  -e DATABASE_HOST=host.docker.internal \
  -e DATABASE_PORT=5432 \
  -e DATABASE_NAME=myproject \
  -e DATABASE_USER=postgres \
  -e DATABASE_PASSWORD=postgres \
  -p 8000:8000 \
  myproject-backend:local

# Full stack via docker compose
docker compose -f deploy/docker-compose.yml up --build
```

In CI/CD, images are built by GitHub Actions:
- **Staging:** pushed to GHCR tagged `staging-<sha>` (by `staging.yml`)
- **Production:** pushed to ECR tagged `vX.Y.Z` + `latest` (by `release.yml`)
