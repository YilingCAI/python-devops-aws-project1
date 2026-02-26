# MyPythonProject1

A production-ready full-stack web application built with FastAPI, Angular, PostgreSQL, and deployed to AWS ECS Fargate via Terraform and GitHub Actions.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Local Development Setup](#local-development-setup)
4. [Environment Configuration](#environment-configuration)
5. [Running Tests](#running-tests)
6. [CI/CD — GitHub Actions](#cicd--github-actions)
7. [Deploying to AWS](#deploying-to-aws)
8. [Conventional Commits & Versioning](#conventional-commits--versioning)
9. [Makefile Reference](#makefile-reference)
10. [Dependency Updates (Dependabot)](#dependency-updates-dependabot)

---

## Architecture Overview

```
Internet
   │
   ▼
Route 53 (DNS)
   │
   ▼
Application Load Balancer  ──────────────┐
(HTTPS :443, HTTP :80 → redirect)        │
   │                                     │
   ├─▶  ECS Fargate — Backend            │
   │    (FastAPI :8000, private subnet)   │
   │          │                          │
   │          ▼                          │
   │    RDS PostgreSQL 16                │
   │    (private DB subnet, Multi-AZ)    │
   │                                     │
   └─▶  ECS Fargate — Frontend           │
        (Nginx serving Angular, :80)     │
                                         │
      AWS Secrets Manager  ◄─────────────┘
      (DB password, JWT secret)
      S3 + DynamoDB  (Terraform state)
      ECR             (Docker images — production)
      GHCR            (Docker images — staging/CI)
```

### Technology Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.12, FastAPI, SQLAlchemy, Alembic, Uvicorn |
| Frontend | Angular 19, TypeScript 5.6, Tailwind CSS 4 |
| Database | PostgreSQL 16 (RDS, Multi-AZ in production) |
| Infrastructure | Terraform 1.5, AWS ECS Fargate, ALB, VPC |
| CI | GitHub Actions — lint, test, security scan, tf plan |
| CD (staging) | GitHub Actions — build GHCR image, tf apply, ECS deploy |
| CD (production) | GitHub Actions — semantic-release, ECR image, ECS deploy |
| Secrets (runtime) | AWS Secrets Manager |
| Secrets (CI/CD) | GitHub Environment secrets |

---

## Repository Structure

```
.
├── README.md                    ← you are here
├── Makefile                     ← unified developer CLI
├── package.json                 ← commitlint + semantic-release (CI tooling)
├── .commitlintrc.yml            ← conventional commit rules
├── .releaserc.json              ← semantic-release config
│
├── backend/                     ← FastAPI application
│   ├── app/
│   │   ├── api/                 ← route handlers (users, games, health)
│   │   ├── core/                ← config, security (JWT), logging
│   │   ├── db/                  ← SQLAlchemy engine, session, base
│   │   ├── models/              ← ORM models
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   └── services/            ← business logic layer
│   ├── alembic/                 ← database migration scripts
│   ├── tests/
│   │   ├── unit/                ← fully mocked, no DB
│   │   └── integration/         ← real DB (auto-rollback)
│   ├── pyproject.toml
│   └── README.md                ← backend-specific setup
│
├── frontend/                    ← Angular SPA
│   ├── src/app/
│   │   ├── components/          ← feature components (login, dashboard, game)
│   │   ├── services/            ← API client, auth, game, user services
│   │   ├── core/                ← auth guard, HTTP interceptor
│   │   └── types/               ← TypeScript interfaces
│   ├── package.json
│   └── README.md                ← frontend-specific setup
│
├── infra/                       ← Terraform infrastructure
│   ├── main.tf                  ← module composition + S3 backend
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── modules/                 ← network, rds, ecs, alb, iam
│   ├── envs/
│   │   ├── staging.tfvars
│   │   └── prod.tfvars
│   └── README.md                ← infra-specific setup and module reference
│
├── config/
│   ├── .env.dev                 ← local Docker Compose only (no secrets)
│   ├── .env.test                ← test env + GitHub Actions CI vars
│   ├── .env.staging             ← staging non-secret config + CI tooling
│   └── .env.production          ← production non-secret config
│
├── deploy/
│   └── docker-compose.yml       ← local full-stack development
│
├── .github/
│   ├── dependabot.yml           ← automated dependency PRs
│   └── workflows/
│       ├── ci.yml               ← CI gate (lint, test, scan, tf plan)
│       ├── staging.yml          ← CD staging (push → develop)
│       ├── release.yml          ← CD production (push tag → v*)
│       └── dependabot-auto-merge.yml
│
├── scripts/                     ← shell helpers called by Makefile
└── docs/                        ← architecture, onboarding, test guide
```

---

## Local Development Setup

### Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| Docker Desktop | 24+ | https://docs.docker.com/desktop/ |
| Python | 3.12+ | `brew install python` |
| Poetry | 1.8+ | `pip install poetry` |
| Node.js | 20 LTS | `brew install node` |
| Terraform | 1.5+ | `brew install terraform` |
| AWS CLI | v2 | `brew install awscli` |
| Make | any | pre-installed on macOS/Linux |

### 1. Clone the repository

```bash
git clone https://github.com/your-org/mypythonproject1.git
cd mypythonproject1
```

### 2. Install all dependencies

```bash
make install
# Equivalent to:
#   cd backend  && poetry install
#   cd frontend && npm ci
#   npm ci  (root — installs commitlint + semantic-release)
```

### 3. Start with Docker Compose (recommended)

This spins up PostgreSQL, the FastAPI backend, and the Angular dev server together:

```bash
cp config/.env.dev deploy/.env       # local env vars (safe, no secrets)
docker compose -f deploy/docker-compose.yml up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:4200 |
| Backend API | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| PostgreSQL | localhost:5432 |

### 4. Run backend only (faster iteration)

```bash
# Terminal 1 — start postgres
docker compose -f deploy/docker-compose.yml up postgres -d

# Terminal 2 — start backend
make backend
# visits http://localhost:8000/docs

# Terminal 3 — start frontend
make frontend
# visits http://localhost:4200
```

### 5. Apply database migrations

```bash
cd backend
poetry run alembic upgrade head
```

---

## Environment Configuration

All non-secret configuration lives in `config/`. Secrets are **never stored in files** — they are injected at runtime via AWS Secrets Manager (production) or GitHub Environment secrets (CI/CD).

| File | Used by | Contents |
|---|---|---|
| `config/.env.dev` | Docker Compose local only | DB host, ports, debug=true |
| `config/.env.test` | pytest + GitHub Actions CI | test DB settings, CI tooling vars |
| `config/.env.staging` | GitHub Actions staging CD | staging endpoints, ECS names |
| `config/.env.production` | GitHub Actions production CD | production endpoints, ECS names |

**Pattern used in GitHub Actions to load an env file:**
```yaml
- name: Load environment
  run: grep -v '^\s*#' config/.env.test | grep -v '^\s*$' >> $GITHUB_ENV
```

**Never put these in config files:**
- Database passwords
- JWT secret keys
- AWS access keys
- API tokens

---

## Running Tests

```bash
# All tests
make test

# Backend only
make backend-test

# Backend — unit tests only (fast, no DB required)
cd backend && poetry run pytest tests/unit -m unit -v

# Backend — integration tests only (requires running postgres)
cd backend && poetry run pytest tests/integration -m integration -v

# With coverage report
cd backend && poetry run pytest --cov=app --cov-report=html
open backend/htmlcov/index.html

# Frontend
make frontend-test
```

See [docs/TEST_ARCHITECTURE.md](docs/TEST_ARCHITECTURE.md) for the full testing strategy.

---

## CI/CD — GitHub Actions

Three workflows handle the full CI/CD pipeline:

```
Feature branch → PR → develop → main
      │            │      │        │
      │            │      │        └─ release.yml (semantic-release → v* tag → prod deploy)
      │            │      └─────────  staging.yml (build → tf apply staging → ECS deploy)
      │            └────────────────  ci.yml      (lint, test, scan, tf plan — quality gate)
      └─────────────────────────────  ci.yml      (same, runs on PR)
```

### Workflow 1 — `ci.yml` (CI Gate)

**Triggers:** `pull_request` → `main`/`develop`, `push` → `main`/`develop`

| Job | What it does |
|---|---|
| `commitlint` | Validates all PR commits follow Conventional Commits spec |
| `changes` | Detects which paths changed (backend/frontend/infra) to skip unaffected jobs |
| `backend-ci` | Ruff lint, unit tests, integration tests against postgres service container |
| `frontend-ci` | ESLint, TypeScript type-check, Angular build |
| `security-scan` | Trivy filesystem scan (SARIF → GitHub Security), GitGuardian secret scan |
| `dependency-audit` | Snyk for Python + Node.js at `--severity-threshold=high` |
| `terraform-plan` | `terraform fmt` check, `validate`, `plan` for staging + prod (PR only, never applies) |
| `quality-gate` | Aggregates all results; single required status check for branch protection |

### Workflow 2 — `staging.yml` (CD Staging)

**Triggers:** `push` to `develop`

| Job | What it does |
|---|---|
| `build` | Builds backend + frontend Docker images, pushes to GHCR tagged `staging` + `staging-<sha>` |
| `scan` | Trivy image scan (warn only, non-blocking for staging) |
| `terraform-staging` | `terraform apply` with `envs/staging.tfvars`, remote S3 state |
| `deploy-staging` | `aws ecs update-service --force-new-deployment`, waits for stability |
| `smoke-test` | Hits `$APP_URL/health`, fails the workflow if not HTTP 200 |

### Workflow 3 — `release.yml` (CD Production)

**Triggers:** `push` to `main` → triggers semantic-release; the created `v*` tag → triggers production deploy

| Job | What it does |
|---|---|
| `autoversion` | Analyses commits since last tag, bumps semver, writes `CHANGELOG.md`, creates GitHub Release + git tag |
| `build-production` | Builds images, pushes to **ECR** tagged `vX.Y.Z`, `latest`, `<sha>` |
| `scan-production` | Trivy image scan — **exits 1 on CRITICAL** (hard block for production) |
| `terraform-production` | `terraform apply` with `envs/prod.tfvars`, requires manual approval via GitHub Environment |
| `deploy-production` | ECS task definition render + deploy, waits for stability |
| `smoke-test-production` | Health check against production URL |

---

## Deploying to AWS

### First-time AWS Bootstrap

Before any deployment you need to create the Terraform remote state resources and GitHub OIDC provider. Run this once per AWS account:

```bash
# 1. Configure AWS CLI
aws configure
# AWS Access Key ID: ...
# AWS Secret Access Key: ...
# Default region: us-east-1

# 2. Create S3 bucket for Terraform state (replace with your bucket name)
aws s3api create-bucket \
  --bucket myproject-terraform-state \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket myproject-terraform-state \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket myproject-terraform-state \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# 3. Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# 4. Create GitHub OIDC provider in IAM (run once per account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### GitHub Repository Secrets & Variables

Go to **Settings → Secrets and variables** in your GitHub repo and configure:

**Repository Variables** (non-secret, visible in logs):
| Variable | Example value | Used by |
|---|---|---|
| `DATABASE_USER` | `postgres` | `ci.yml` postgres service container |
| `DATABASE_NAME` | `testdb` | `ci.yml` postgres service container |
| `DATABASE_PORT` | `5432` | `ci.yml` postgres service container |

**Repository Secrets** (encrypted, never logged):
| Secret | Description |
|---|---|
| `GITGUARDIAN_API_KEY` | GitGuardian secret scanning token |
| `SNYK_TOKEN` | Snyk vulnerability scanning token |

**`staging` Environment Secrets** (Settings → Environments → staging):
| Secret | Description |
|---|---|
| `AWS_ROLE_TO_ASSUME` | ARN of IAM role for staging (`arn:aws:iam::123456:role/github-staging`) |
| `TERRAFORM_STATE_BUCKET` | S3 bucket name for Terraform state |
| `TERRAFORM_LOCK_TABLE` | DynamoDB table name for state locks |
| `DATABASE_PASSWORD` | RDS staging database password |

**`production` Environment Secrets** (Settings → Environments → production):
| Secret | Description |
|---|---|
| `AWS_ROLE_TO_ASSUME` | ARN of IAM role for production |
| `AWS_REGION` | `us-east-1` |
| `TERRAFORM_STATE_BUCKET` | S3 bucket name |
| `TERRAFORM_LOCK_TABLE` | DynamoDB table name |
| `APP_URL` | `https://myproject.com` |
| `ECS_CLUSTER` | `myproject-prod-cluster` |
| `ECS_SERVICE_PREFIX` | `myproject-prod` |
| `ECS_TASK_DEFINITION` | path to task def JSON |
| `TF_VERSION` | `1.5.0` |

> **Tip:** Set a required reviewer on the `production` environment under Settings → Environments → Required reviewers. This creates a manual approval gate before `terraform-production` and `deploy-production` run.

### Deploying to Staging (automatic)

```bash
# Simply merge a PR into develop — staging.yml triggers automatically
git checkout develop
git merge feature/my-feature
git push origin develop

# Watch the deployment at:
# https://github.com/your-org/mypythonproject1/actions/workflows/staging.yml
```

### Deploying to Production (tag-driven)

```bash
# Merge your release branch into main — semantic-release creates the tag automatically
git checkout main
git merge develop
git push origin main

# semantic-release will:
#   1. Analyse commits since last tag
#   2. Determine bump: feat → minor, fix → patch, BREAKING CHANGE → major
#   3. Write CHANGELOG.md and commit it
#   4. Create git tag (e.g. v1.3.0)
#   5. Create GitHub Release

# The v1.3.0 tag push triggers release.yml → production deploy
# Monitor at:
# https://github.com/your-org/mypythonproject1/actions/workflows/release.yml
```

### Manual Terraform operations

```bash
# Staging — plan only (safe, read-only)
make tf-plan ENV=staging

# Staging — apply (will modify AWS resources)
make tf-apply ENV=staging

# Production — always plan first and review carefully
make tf-plan ENV=prod
make tf-apply ENV=prod

# Destroy (destructive — requires confirmation)
make tf-destroy ENV=staging
```

---

## Conventional Commits & Versioning

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/) spec. This is enforced by `commitlint` on every PR.

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit types and their effect on version bumps

| Type | Semver bump | Example |
|---|---|---|
| `feat` | minor (`1.2.0 → 1.3.0`) | `feat(auth): add OAuth2 login` |
| `fix` | patch (`1.2.0 → 1.2.1`) | `fix(api): handle null user id` |
| `perf` | patch | `perf(db): add index on user email` |
| `refactor` | patch | `refactor(services): extract user factory` |
| `revert` | patch | `revert: feat(auth): add OAuth2 login` |
| `docs` | no release | `docs: update deployment guide` |
| `style` | no release | `style: fix trailing whitespace` |
| `test` | no release | `test: add user service unit tests` |
| `build` | no release | `build(deps): bump fastapi to 0.128` |
| `ci` | no release | `ci: add trivy scan step` |
| `chore` | no release | `chore: clean up old env files` |
| `BREAKING CHANGE` footer | major (`1.2.0 → 2.0.0`) | `feat!: remove v1 API endpoints` |

### Example workflow

```bash
# Good commit examples
git commit -m "feat(game): add multiplayer room support"
git commit -m "fix(auth): refresh token not invalidated on logout"
git commit -m "ci: increase backend test timeout to 10 minutes"

# Breaking change
git commit -m "feat(api)!: rename /users to /accounts

BREAKING CHANGE: all /users endpoints moved to /accounts"
```

---

## Makefile Reference

```bash
make help            # list all targets

# Development
make install         # install backend + frontend + root deps
make dev             # start all services via docker compose
make backend         # run FastAPI dev server only
make frontend        # run Angular dev server only

# Testing
make test            # run all tests
make backend-test    # pytest (backend)
make frontend-test   # ng test (frontend)
make lint            # ruff + eslint
make format          # ruff format + prettier

# Infrastructure
make tf-validate ENV=staging          # fmt check + validate
make tf-plan     ENV=staging          # plan (read-only, safe)
make tf-apply    ENV=staging          # apply (modifies AWS)
make tf-destroy  ENV=staging          # destroy (destructive)

# Docker
make docker-build ENV=staging IMAGE_TAG=v1.0.0
make docker-push  ENV=staging IMAGE_TAG=v1.0.0
```

---

## Dependency Updates (Dependabot)

Dependabot is configured (`.github/dependabot.yml`) to automatically open PRs for:

| Ecosystem | Location | Schedule |
|---|---|---|
| Poetry (Python) | `/backend` | Weekly, Mondays |
| npm (Node.js) | `/frontend` | Weekly, Mondays |
| Terraform providers | `/infra` | Weekly, Tuesdays |
| GitHub Actions | `/` | Weekly, Wednesdays |

Dependabot PRs for patch/minor updates are automatically merged by `dependabot-auto-merge.yml` after CI passes. Major version bumps require manual review.
