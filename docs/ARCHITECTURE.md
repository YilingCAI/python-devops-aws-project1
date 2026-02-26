# Architecture

This document describes the full system architecture of MyPythonProject1 — how services are structured, how they communicate, how infrastructure is provisioned, and how code moves from a developer's machine to production.

---

## System Diagram

```
Developer Workstation
        │
        │  git push
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       GitHub Repository                         │
│                                                                 │
│  Branches:  feature/* ──► develop ──► main ──► v* tag          │
│                                                                 │
│  Workflows:                                                     │
│    ci.yml            ← runs on every PR and push to main/dev   │
│    staging.yml       ← runs on push to develop                 │
│    release.yml       ← runs on push to main (release) +        │
│                         push of v* tag (production deploy)      │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
        Staging deploy              Production deploy
               │                          │
               ▼                          ▼
   ┌───────────────────┐     ┌─────────────────────────┐
   │ GHCR Docker Image │     │   ECR Docker Image       │
   │ tag: staging-<sha>│     │   tag: v1.3.0, latest    │
   └────────┬──────────┘     └────────────┬─────────────┘
            │                             │
            ▼                             ▼
   ┌─────────────────────────────────────────────────────┐
   │                    AWS (us-east-1)                  │
   │                                                     │
   │  ┌──────────────────────────────────────────────┐   │
   │  │               VPC  10.0.0.0/16               │   │
   │  │                                              │   │
   │  │  Public Subnets (2 AZs)                     │   │
   │  │  ┌─────────────────────────────────────┐    │   │
   │  │  │  Application Load Balancer (ALB)    │    │   │
   │  │  │  :443 HTTPS → backend :8000         │    │   │
   │  │  │  :80  HTTP  → 301 redirect          │    │   │
   │  │  │  NAT Gateway (outbound egress)      │    │   │
   │  │  └────────────────┬────────────────────┘    │   │
   │  │                   │                         │   │
   │  │  Private Subnets (2 AZs)                    │   │
   │  │  ┌────────────────▼────────────────────┐    │   │
   │  │  │  ECS Fargate Cluster                │    │   │
   │  │  │  ┌──────────────────────────────┐   │    │   │
   │  │  │  │ backend service              │   │    │   │
   │  │  │  │ FastAPI + Uvicorn :8000      │   │    │   │
   │  │  │  │ fetches secrets from SM      │   │    │   │
   │  │  │  └──────────────────────────────┘   │    │   │
   │  │  │  ┌──────────────────────────────┐   │    │   │
   │  │  │  │ frontend service             │   │    │   │
   │  │  │  │ Nginx serving Angular :80    │   │    │   │
   │  │  │  └──────────────────────────────┘   │    │   │
   │  │  └────────────────────────────────────┘    │   │
   │  │                                            │   │
   │  │  DB Subnets (isolated, no public route)    │   │
   │  │  ┌─────────────────────────────────────┐   │   │
   │  │  │  RDS PostgreSQL 16 (Multi-AZ prod)  │   │   │
   │  │  │  port 5432, encrypted at rest       │   │   │
   │  │  └─────────────────────────────────────┘   │   │
   │  └──────────────────────────────────────────┘   │
   │                                                 │
   │  Supporting services (not in VPC):              │
   │  ┌──────────────────────────────────────────┐   │
   │  │ Secrets Manager  — DB password, JWT key  │   │
   │  │ ECR              — production images     │   │
   │  │ S3 + DynamoDB    — Terraform state       │   │
   │  │ IAM OIDC         — GitHub Actions auth   │   │
   │  │ CloudWatch Logs  — ECS task logs         │   │
   │  └──────────────────────────────────────────┘   │
   └─────────────────────────────────────────────────┘
```

---

## Application Layers

### Backend (FastAPI)

```
app/
├── api/          ← Route handlers (thin controllers — validate input, call service, return response)
│   ├── health.py ← GET /health  (used by ALB health checks + smoke tests)
│   ├── user.py   ← POST /users, GET /users/me, etc.
│   └── game.py   ← CRUD + game logic endpoints
├── core/
│   ├── config.py ← pydantic-settings reads env vars, validates types at startup
│   ├── security.py ← JWT creation/verification, password hashing (bcrypt/argon2)
│   └── logging.py  ← JSON structured logging
├── db/
│   ├── session.py  ← async SQLAlchemy session factory, dependency injector
│   └── base.py     ← declarative base, shared metadata
├── models/         ← SQLAlchemy ORM models (database schema)
├── schemas/        ← Pydantic models (API contract — request/response shapes)
└── services/       ← Business logic (no HTTP, no DB calls — pure functions + repo calls)
```

**Request lifecycle:**
```
HTTP request
  → ALB
  → ECS Fargate container (Uvicorn ASGI)
  → FastAPI router (api/)
  → Pydantic schema validation
  → Service layer (services/)
  → SQLAlchemy session (db/session.py)
  → PostgreSQL
  → Pydantic response schema
  → HTTP response
```

### Frontend (Angular)

```
src/app/
├── components/        ← Feature UI (login, register, dashboard, game)
├── services/
│   ├── api.service.ts ← Base HTTP client with error handling
│   ├── auth.service.ts ← Login, logout, token storage
│   └── game.service.ts ← Game CRUD via API
├── core/
│   ├── auth.guard.ts        ← Redirects unauthenticated users to /login
│   └── http.interceptor.ts  ← Attaches Bearer token to every API request
└── types/              ← Shared TypeScript interfaces
```

### Database (PostgreSQL)

- Migrations managed by **Alembic** (`backend/alembic/versions/`)
- Applied automatically on each deploy before ECS tasks start
- In production: Multi-AZ RDS, automated daily backups, encrypted at rest with KMS
- In staging: single-AZ RDS, daily backups, encrypted
- In tests: ephemeral PostgreSQL Docker container, auto-rollback after each test

---

## Infrastructure (Terraform)

Infrastructure is split into reusable modules:

| Module | Resources |
|---|---|
| `modules/network` | VPC, public/private/DB subnets, IGW, NAT Gateway, route tables, NACLs |
| `modules/alb` | ALB, target groups, listeners (HTTP→HTTPS redirect, HTTPS forward) |
| `modules/ecs` | ECS cluster, backend + frontend task definitions, IAM execution role |
| `modules/rds` | RDS PostgreSQL instance, subnet group, security group, KMS key |
| `modules/iam` | GitHub OIDC provider, CI/CD IAM roles (staging/production) |

Environment-specific values live in `infra/envs/staging.tfvars` and `infra/envs/prod.tfvars`. The Terraform code itself is environment-agnostic.

Remote state is stored in S3 with DynamoDB locking. The backend block uses **partial configuration** so bucket/key/region are injected at `terraform init` time by CI workflows:

```bash
terraform init \
  -backend-config="bucket=myproject-terraform-state" \
  -backend-config="key=staging/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=terraform-locks"
```

---

## Security Model

### Secrets — Never in code

| Secret type | Where stored | How accessed |
|---|---|---|
| DB password | AWS Secrets Manager | ECS task IAM role at container startup |
| JWT secret | AWS Secrets Manager | ECS task IAM role at container startup |
| CI/CD AWS credentials | GitHub OIDC (no static keys) | `aws-actions/configure-aws-credentials` |
| Staging secrets | GitHub Environment "staging" | Workflow `${{ secrets.* }}` |
| Production secrets | GitHub Environment "production" | Workflow `${{ secrets.* }}` with required reviewer approval |

### Network — Least privilege

- ECS tasks run in **private subnets** — no inbound internet access
- Only the ALB (in public subnet) is internet-facing
- RDS is in **DB subnets** — only the ECS security group can reach port 5432
- All inter-service traffic is within the VPC
- All egress from private subnets routes through the NAT Gateway

### IAM — OIDC, no static keys

GitHub Actions authenticates to AWS using an **OIDC identity provider** — no IAM user access keys are stored anywhere. Each environment has a dedicated IAM role with the minimum permissions required for that environment.

---

## CI/CD Flow — End to End

```
Developer writes code on feature branch
        │
        │ git push origin feature/add-game-mode
        ▼
Pull Request opened → develop
        │
        ├─ ci.yml triggered
        │     commitlint:       all commits follow Conventional Commits?
        │     backend-ci:       ruff lint → unit tests → integration tests
        │     frontend-ci:      eslint → tsc → ng build
        │     security-scan:    trivy fs + gitguardian
        │     dependency-audit: snyk python + node
        │     terraform-plan:   staging + prod (read-only, comments plan on PR)
        │     quality-gate:     aggregates all — single required status check
        │
        ├─ Code review + approval
        │
        ▼
PR merged to develop
        │
        ├─ ci.yml triggered again (post-merge validation)
        │
        └─ staging.yml triggered
              build:             docker build backend + frontend → GHCR
              scan:              trivy image scan (warn only)
              terraform-staging: terraform apply envs/staging.tfvars
              deploy-staging:    ecs update-service --force-new-deployment
              smoke-test:        curl $APP_URL/health → must return 200

        ▼
When ready to release: merge develop → main
        │
        ├─ ci.yml triggered
        │
        └─ release.yml triggered (push to main)
              autoversion:  semantic-release analyses commits
                            → bumps version (e.g. 1.2.0 → 1.3.0)
                            → writes CHANGELOG.md
                            → commits + creates tag v1.3.0
                            → creates GitHub Release

        ▼
Tag v1.3.0 pushed
        │
        └─ release.yml triggered (push tag v*)
              build-production:      docker build → ECR tagged v1.3.0 + latest
              scan-production:       trivy — CRITICAL = hard block
              terraform-production:  [manual approval required] → terraform apply prod
              deploy-production:     ecs task definition update + deploy
              smoke-test-production: curl $PROD_URL/health → must return 200
```
