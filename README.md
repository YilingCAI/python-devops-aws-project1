# Full-Stack DevOps Portfolio — Multi-Strategy Deployment

> A production-grade full-stack application deployed three different ways to AWS, demonstrating the trade-offs between EC2, ECS Fargate, and EKS (Kubernetes) as deployment targets.

---

## Table of Contents

- [Full-Stack DevOps Portfolio — Multi-Strategy Deployment](#full-stack-devops-portfolio--multi-strategy-deployment)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Repository Structure](#repository-structure)
  - [Application Stack](#application-stack)
  - [Architecture Overview](#architecture-overview)
    - [EC2 + ALB (ec2-alb-infra)](#ec2--alb-ec2-alb-infra)
    - [ECS Fargate (ecs-infra)](#ecs-fargate-ecs-infra)
    - [EKS + ArgoCD (eks-infra + gitops-argocd)](#eks--argocd-eks-infra--gitops-argocd)
  - [Deployment Strategy Comparison](#deployment-strategy-comparison)
  - [CI/CD Pipeline](#cicd-pipeline)
  - [Local Development](#local-development)
    - [Prerequisites](#prerequisites)
    - [Backend](#backend)
    - [Frontend](#frontend)
    - [Full stack with Docker Compose](#full-stack-with-docker-compose)
  - [Environment Variables](#environment-variables)
    - [Backend (`config/.env.dev`)](#backend-configenvdev)
    - [Frontend](#frontend-1)
  - [API Reference](#api-reference)
    - [Health](#health)
    - [Users](#users)
    - [Games](#games)
  - [Folder Structure](#folder-structure)
  - [Testing](#testing)
  - [Future Improvements](#future-improvements)

---

## Project Overview

This project deploys the a simple **same Angular + FastAPI fullstack application** across three distinct AWS infrastructure patterns using Terraform, Ansible, Kubernetes, and ArgoCD. The goal is to demonstrate different deployment strategy choices - a core skill set for senior DevOps and SRE roles.
Each deployment strategy has three different environment (dev, staging and prod) inline with real entreprise production SRE, DevOps standards. 

**The application** is a game platform with user registration/authentication, game session management, and a PostgreSQL backend.

---

## Repository Structure

| Repository | Purpose |
|---|---|
| **`app`** (this repo) | Angular 19 frontend + FastAPI backend source code, Docker images, CI workflows | 
| **`ec2-alb-infra`** | Terraform + Ansible: EC2 Auto Scaling Groups behind an ALB, Nginx as reverse proxy | https://github.com/YilingCAI/python-angular-project1-infra3.git 
| **`ecs-infra`** | Terraform: ECS Fargate containers, ALB, service discovery | https://github.com/YilingCAI/python-angular-project1-infra1.git 
| **`eks-infra`** | Terraform: EKS cluster, VPC, RDS, Helm add-ons | https://github.com/YilingCAI/python-angular-project1-infra2.git 
| **`gitops-argocd`** | Helm charts + ArgoCD App-of-Apps pattern for GitOps deployments on EKS | https://github.com/YilingCAI/python-angular-project1-gitops.git 

Each infra repo has its own `environments/dev`, `environments/staging`, and `environments/prod` directories with per-environment Terraform variable files.

---

## Application Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 19, Tailwind CSS |
| Backend | Python 3.12, FastAPI 0.128, Uvicorn |
| ORM / Migrations | SQLAlchemy 2.0, Alembic |
| Auth | JWT (python-jose), bcrypt |
| Database | PostgreSQL 17 (AWS RDS) |
| Containerization | Docker, AWS ECR |
| Infrastructure | Terraform ≥ 1.10, AWS Provider ~> 6.0 |
| Config Management | Ansible 2.x |
| Orchestration | Kubernetes (EKS), Helm 3 |
| GitOps | ArgoCD, App-of-Apps pattern |
| CI/CD | GitHub Actions |
| Monitoring | CloudWatch, Prometheus, Grafana |

---

## Architecture Overview

### EC2 + ALB (ec2-alb-infra)

```
Internet
    │
    ▼
┌─────────────────────────────────┐
│  Application Load Balancer      │
│  port 80 → Nginx (EC2)          │
│  /users/* /games/* → FastAPI    │
└────────────┬────────────────────┘
             │
    ┌────────▼────────────────────────┐
    │  Private Subnets                │
    │  ┌──────────────────────────┐   │
    │  │  Backend ASG             │   │
    │  │  EC2 → FastAPI :8000     │   │
    │  └──────────────────────────┘   │
    │  ┌──────────────────────────┐   │
    │  │  Frontend ASG            │   │
    │  │  EC2 → Nginx :80         │   │
    │  │  (serves Angular SPA)    │   │
    │  └──────────────────────────┘   │
    └─────────────────────────────────┘
             │
    ┌────────▼────────┐
    │  Database Subnet │
    │  RDS PostgreSQL  │
    └─────────────────┘
```

Ansible handles app deployment: pulls Docker images from ECR, extracts Angular static files to Nginx, and runs FastAPI via Docker Compose.

---

### ECS Fargate (ecs-infra)

```
Internet
    │
    ▼
┌─────────────────────────────┐
│  Application Load Balancer  │
└────────────┬────────────────┘
             │
    ┌────────▼────────────────────────┐
    │  ECS Cluster (Fargate)          │
    │  ┌──────────────────────────┐   │
    │  │  backend service         │   │
    │  │  Task: FastAPI container │   │
    │  └──────────────────────────┘   │
    │  ┌──────────────────────────┐   │
    │  │  frontend service        │   │
    │  │  Task: Nginx + Angular   │   │
    │  └──────────────────────────┘   │
    └─────────────────────────────────┘
             │
    ┌────────▼────────┐
    │  RDS PostgreSQL  │
    └─────────────────┘
```

No servers to manage. ECS handles container scheduling, health replacement, and rolling deployments.

---

### EKS + ArgoCD (eks-infra + gitops-argocd)

```
GitHub Actions                  ArgoCD (in-cluster)
push → CI → ECR  ──────────►  App-of-Apps
update Helm values               │
                                 ├── dev namespace
                                 │    ├─ backend Deployment
                                 │    └─ frontend Deployment
                                 ├── staging namespace
                                 │    ├─ backend Deployment
                                 │    └─ frontend Deployment
                                 └── prod namespace (manual sync)
                                      ├─ backend Deployment
                                      └─ frontend Deployment
                                              │
                                         RDS PostgreSQL
```

GitOps: the cluster state is driven by the `gitops-argocd` repo. ArgoCD continuously reconciles. Prod deployments require a manual approval gate.

---

## Deployment Strategy Comparison

| | EC2 + ALB | ECS Fargate | EKS + ArgoCD |
|---|---|---|---|
| **Compute** | EC2 instances | Serverless containers | Kubernetes pods |
| **Scaling** | ASG (instance-level) | Task-level auto-scaling | HPA + Cluster Autoscaler |
| **Deployment** | Ansible push | ECS rolling update | GitOps (ArgoCD sync) |
| **Infra complexity** | Medium | Low | High |
| **Operational overhead** | High (OS patching) | Low | Medium (K8s expertise) |
| **Config management** | Ansible roles | Task definitions | Helm charts |
| **Secrets** | AWS Secrets Manager | ECS secrets injection | Kubernetes Secrets |
| **Observability** | CloudWatch + Nginx logs | CloudWatch Container Insights | Prometheus + Grafana |
| **Best for** | Legacy lift-and-shift | Simpler containerised apps | Microservices at scale |

---

## CI/CD Pipeline

All three strategies share the **same CI pipeline** in this repo. Docker images are built once and promoted across environments by Git SHA.

```
On pull request:
  ci.yml ──► lint ──► test ──► build (no push)

On merge to main:
  _build-and-push.yml ──► ECR (tagged: git SHA)
         │
         ├──► cd-ec2-ansible.yml  ──► Ansible deploy to EC2 ASGs
         ├──► cd-ecs-fargate.yml  ──► terraform apply (ECS task update)
         └──► cd-eks-gitops.yml   ──► update Helm image tag
                                      ArgoCD auto-sync (dev/staging)
                                      Manual gate (prod)
```

Infrastructure changes in the infra repos trigger their own Terraform plan/apply workflows on `.tf` file changes. A daily `terraform-drift.yml` detects out-of-band changes across all environments.

---

## Local Development

### Prerequisites

- Python 3.12+, Node.js 20+, Docker, PostgreSQL client (`psql`)

### Backend

```bash
cd backend

# Install with dev dependencies
pip install -e ".[dev]"

# Configure environment
cp config/.env.dev.example config/.env.dev
# Edit config/.env.dev with your local DB credentials

# Run migrations
alembic upgrade head

# Start dev server (auto-reload)
uvicorn main:app --reload --port 8000
```

Interactive docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend

npm install

# Start dev server
ng serve --port 4200
```

App: `http://localhost:4200`

### Full stack with Docker Compose

```bash
docker compose -f deploy/docker-compose.yml up --build
```

---

## Environment Variables

### Backend (`config/.env.dev`)

| Variable | Description | Default |
|---|---|---|
| `DATABASE_HOST` | PostgreSQL host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_NAME` | Database name | `gamedb` |
| `DATABASE_USER` | Database user | `postgres` |
| `DATABASE_PASSWORD` | Database password | *(required)* |
| `JWT_SECRET_KEY` | JWT signing secret | *(required)* |
| `JWT_ALGORITHM` | Signing algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Access token TTL | `30` |
| `JWT_REFRESH_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:4200` |
| `ENVIRONMENT` | Runtime environment | `dev` |
| `AWS_REGION` | AWS region (Secrets Manager) | `us-east-1` |

### Frontend

The Angular app reads `window.API_BASE_URL` at runtime. When empty it calls the API on the same origin (through the ALB or a local dev proxy).

---

## API Reference

All routes are served on the same origin. The ALB routes `/users/*` and `/games/*` to the FastAPI backend; everything else hits Nginx (Angular SPA).

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health/` | Combined liveness + readiness |
| `GET` | `/health/live` | Liveness probe (returns uptime) |
| `GET` | `/health/ready` | Readiness probe (checks DB) |

### Users

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/users/register` | — | Register a new account |
| `POST` | `/users/login` | — | Login, returns JWT tokens |
| `GET` | `/users/me` | Bearer | Get current user profile |

### Games

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/games/create_game` | Bearer | Create a new game session |

---

## Folder Structure

```
mypythonproject1/          ← this repo
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers (health, users, game)
│   │   ├── core/          # Config, logging, security
│   │   ├── db/            # Database session factory
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   └── services/      # Business logic layer
│   ├── alembic/           # Database migration scripts
│   ├── tests/
│   │   ├── integration/   # Full API endpoint tests (with DB)
│   │   └── unit/          # Service and model unit tests
│   ├── main.py            # FastAPI app entry point
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── services/  # ApiClient, AuthService
│   │   │   └── models/
│   │   └── environments/  # environment.ts, environment.prod.ts
│   ├── angular.json
│   └── package.json
├── deploy/
│   └── docker-compose.yml
└── .github/
    └── workflows/
        ├── ci.yml                  # Lint, test, build on PR
        ├── _build-and-push.yml     # Reusable: build + push to ECR
        ├── _smoke-test.yml         # Reusable: post-deploy smoke test
        ├── cd-ec2-ansible.yml      # Deploy via Ansible to EC2
        ├── cd-ecs-fargate.yml      # Deploy to ECS Fargate
        └── cd-eks-gitops.yml       # Update Helm values → ArgoCD sync
```

---

## Testing

```bash
# Backend — full test suite
cd backend
pytest

# Backend — with HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend — unit tests (headless)
cd frontend
ng test --watch=false --browsers=ChromeHeadless

# Frontend — lint
ng lint
```

The CI pipeline runs both suites on every pull request before any build or deploy step executes.

---

## Future Improvements

- [ ] **Blue/green deployments** — CodeDeploy on ECS; Argo Rollouts on EKS
- [ ] **HTTPS everywhere** — ACM certificates + HTTPS ALB listeners (HTTP used for dev)
- [ ] **Centralised secrets** — AWS Secrets Manager CSI driver for Kubernetes; Vault integration
- [ ] **Infrastructure testing** — Terratest for Terraform module validation
- [ ] **Multi-region** — Active-active RDS with Route 53 latency routing
- [ ] **Distributed tracing** — AWS X-Ray across all three deployment strategies
- [ ] **Cost optimisation** — Spot instances for non-prod EC2 ASGs and EKS node groups
- [ ] **Service mesh** — Istio or AWS App Mesh for mTLS between microservices
---