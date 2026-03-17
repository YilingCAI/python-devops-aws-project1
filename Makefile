###############################################################################
# Makefile — Local developer CLI for mypythonproject1
#
# Wraps common operations so engineers don't need to remember long commands:
#   - Docker Compose local environment  (docker-up / docker-down)
#   - Backend / frontend development server  (make dev)
#   - Test runners  (make test, backend-test-*, frontend-test, frontend-build)
#   - Linting  (make lint)
#   - Terraform local plan/apply/destroy  (make tf-*  ENV=staging|prod)
#   - Docker build + ECR push  (make docker-build / docker-push  ENV=...)
#   - ECS rolling deploy  (make ecs-deploy  ENV=...  IMAGE_TAG=...)
#   - One-time AWS infra bootstrap  (make bootstrap)
#   - Environment variable setup  (make setup-env  ENV=...)
#
# All deployment targets require real AWS credentials in the shell.
# Terraform targets delegate to scripts/terraform-*.sh.
###############################################################################
.PHONY: help install dev docker-up docker-down docker-logs \
	test backend-test frontend-test frontend-build lint clean \
	ensure-backend-venv ensure-frontend-deps \
	bootstrap setup-env \
	tf-validate tf-plan tf-apply tf-destroy \
	docker-build docker-push ecs-deploy deploy deploy-staging deploy-prod

# ============================================================================
# COLORS & FORMATTING
# ============================================================================
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ============================================================================
# LOCAL ENV / TFVARS LOADING (dev by default)
# ============================================================================

ENV_FILE := deploy/.env
INFRA_ROOT ?= ../mypythonproject1-infra
DEV_TFVARS_FILE := $(INFRA_ROOT)/environments/dev/terraform.tfvars

-include $(ENV_FILE)

# Prefer tfvars as source of truth for infra variables.
TFVARS_ENV := $(shell awk -F'=' '/^environment[[:space:]]*=/{gsub(/["[:space:]]/,"",$$2); print $$2; exit}' $(DEV_TFVARS_FILE) 2>/dev/null)
ENV ?= $(or $(TFVARS_ENV),dev)
TFVARS_FILE = $(INFRA_ROOT)/environments/$(ENV)/terraform.tfvars

TFVARS_PROJECT_NAME := $(shell awk -F'=' '/^project_name[[:space:]]*=/{gsub(/["[:space:]]/,"",$$2); print $$2; exit}' $(TFVARS_FILE) 2>/dev/null || awk -F'=' '/^project_name[[:space:]]*=/{gsub(/["[:space:]]/,"",$$2); print $$2; exit}' $(DEV_TFVARS_FILE) 2>/dev/null)
TFVARS_AWS_REGION := $(shell awk -F'=' '/^aws_region[[:space:]]*=/{gsub(/["[:space:]]/,"",$$2); print $$2; exit}' $(TFVARS_FILE) 2>/dev/null || awk -F'=' '/^aws_region[[:space:]]*=/{gsub(/["[:space:]]/,"",$$2); print $$2; exit}' $(DEV_TFVARS_FILE) 2>/dev/null)

PROJECT_NAME := $(or $(TFVARS_PROJECT_NAME),$(PROJECT_NAME),mypythonproject1)
AWS_REGION := $(or $(TFVARS_AWS_REGION),$(AWS_REGION),us-east-1)
DOCKER_PLATFORM ?= linux/amd64

ECS_CLUSTER ?= $(PROJECT_NAME)-cluster-$(ENV)
ECS_SERVICE_BACKEND ?= backend-service-$(ENV)
ECS_SERVICE_FRONTEND ?= frontend-service-$(ENV)

TERRAFORM_STATE_BUCKET ?= terraform-state-$(AWS_ACCOUNT_ID)
TERRAFORM_LOCK_TABLE ?= terraform-locks

ifeq ($(strip $(AWS_ACCOUNT_ID)),)
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
endif

BACKEND_VENV_PY := backend/.venv/bin/python

# ============================================================================
# HELP & DOCUMENTATION
# ============================================================================

help:
	@echo ""
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║    DevOps Makefile - Production-Ready Development Setup       ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)🐳 DOCKER COMPOSE (Recommended for local development)$(NC)"
	@echo "  $(YELLOW)make docker-up$(NC)            - Start all services (db, backend, frontend)"
	@echo "  $(YELLOW)make docker-down$(NC)          - Stop all services"
	@echo "  $(YELLOW)make docker-logs$(NC)          - View Docker Compose logs"
	@echo "  $(YELLOW)make docker-clean$(NC)         - Remove volumes and containers"
	@echo ""
	@echo "$(GREEN)🔧 LOCAL DEVELOPMENT (Without Docker)$(NC)"
	@echo "  $(YELLOW)make install$(NC)              - Install dependencies (backend & frontend)"
	@echo "  $(YELLOW)make dev$(NC)                  - Run backend & frontend (local)"
	@echo "  $(YELLOW)make backend$(NC)              - Run backend only"
	@echo "  $(YELLOW)make frontend$(NC)             - Run frontend only"
	@echo ""
	@echo "$(GREEN)🧪 TESTING & QUALITY$(NC)"
	@echo "  $(YELLOW)make test$(NC)                 - Run all tests (unit + integration + frontend)"
	@echo "  $(YELLOW)make backend-test$(NC)         - Run all backend tests (unit + integration)"
	@echo "  $(YELLOW)make backend-test-unit$(NC)    - Unit tests only (no DB, fast)"
	@echo "  $(YELLOW)make backend-test-integration$(NC) - Integration tests (real DB)"
	@echo "  $(YELLOW)make backend-test-coverage$(NC) - Tests with coverage report"
	@echo "  $(YELLOW)make backend-validate-tests$(NC) - Validate test configuration"
	@echo "  $(YELLOW)make frontend-test$(NC)        - Frontend tests (Karma/Jasmine)"
	@echo "  $(YELLOW)make frontend-build$(NC)       - TypeScript type-check + production build (mirrors CI)"
	@echo "  $(YELLOW)make lint$(NC)                 - Ruff lint+format-check (backend) + ESLint + type-check (frontend)"
	@echo ""
	@echo "$(GREEN)⚙️  SETUP$(NC)"
	@echo "  $(YELLOW)make bootstrap$(NC)            - Terraform bootstrap (ECR, IAM, S3, optional DynamoDB lock table)"
	@echo "  $(YELLOW)make setup-env$(NC)            - Export env vars for Terraform/deploy (ENV=staging|prod|dev)"
	@echo ""
	@echo "$(GREEN)🐳 DOCKER BUILD & PUSH$(NC)"
	@echo "  $(YELLOW)make docker-build$(NC)         - Build Docker images (ENV=staging|prod)"
	@echo "  $(YELLOW)make docker-push$(NC)          - Push to ECR (ENV=staging|prod)"
	@echo ""
	@echo "$(GREEN)🚀 DEPLOYMENT$(NC)"
	@echo "  $(YELLOW)make deploy$(NC)               - Full deploy (ENV=staging|prod IMAGE_TAG=...)"
	@echo "  $(YELLOW)make deploy-staging$(NC)       - Deploy to staging"
	@echo "  $(YELLOW)make deploy-prod$(NC)          - Deploy to production"
	@echo ""
	@echo "$(GREEN)🧹 CLEANUP$(NC)"
	@echo "  $(YELLOW)make clean$(NC)                - Remove build artifacts"
	@echo ""
	@echo "$(YELLOW)📝 EXAMPLES:$(NC)"
	@echo "  $(BLUE)make docker-up$(NC)              # Start dev environment with Docker"
	@echo "  $(BLUE)make backend-test$(NC)           # Run tests locally"
	@echo "  $(BLUE)make deploy ENV=staging IMAGE_TAG=v1.0.0$(NC)"
	@echo ""

# ============================================================================
# DOCKER COMPOSE DEVELOPMENT
# ============================================================================

docker-up:
	@echo "$(GREEN)🐳 Starting Docker Compose services...$(NC)"
	cd deploy && docker compose --env-file .env up -d
	@echo ""
	@echo "$(GREEN)✅ Services started!$(NC)"
	@echo ""
	@echo "$(BLUE)Access points:$(NC)"
	@echo "  Frontend:    $(BLUE)http://localhost:4200$(NC)"
	@echo "  Backend:     $(BLUE)http://localhost:8000$(NC)"
	@echo "  Database:    $(BLUE)postgresql://localhost:5432$(NC)"
	@echo ""
	@echo "$(YELLOW)Tip: Use 'make docker-logs' to view logs$(NC)"

docker-down:
	@echo "$(YELLOW)⬇️  Stopping Docker Compose services...$(NC)"
	cd deploy && docker compose --env-file .env down
	@echo "$(GREEN)✅ Services stopped$(NC)"

docker-restart:
	@echo "$(YELLOW)🔄 Restarting Docker Compose services...$(NC)"
	cd deploy && docker compose --env-file .env restart
	@echo "$(GREEN)✅ Services restarted$(NC)"

docker-logs:
	cd deploy && docker compose --env-file .env logs -f

docker-logs-backend:
	cd deploy && docker compose --env-file .env logs -f backend

docker-logs-frontend:
	cd deploy && docker compose --env-file .env logs -f frontend

docker-logs-db:
	cd deploy && docker compose --env-file .env logs -f postgres

docker-clean:
	@echo "$(RED)🧹 Removing Docker Compose volumes and containers...$(NC)"
	cd deploy && docker compose --env-file .env down -v
	@echo "$(GREEN)✅ Cleaned$(NC)"

docker-ps:
	@echo "$(BLUE)Docker Compose Services:$(NC)"
	cd deploy && docker compose --env-file .env ps

# ============================================================================
# LOCAL DEVELOPMENT (Without Docker)
# ============================================================================

install:
	@echo "$(GREEN)📦 Installing dependencies...$(NC)"
	cd backend && pip install -e .
	cd frontend && npm install
	cd .github && npm ci --ignore-scripts
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

dev:
	@echo "$(GREEN)🚀 Starting development environment...$(NC)"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:4200"
	@echo ""
	@echo "$(YELLOW)Make sure PostgreSQL is running locally (or use 'make docker-up')!$(NC)"
	@echo ""
	@(cd backend && python -m uvicorn main:app --reload) & \
	(cd frontend && ng serve --open)

backend:
	@echo "$(GREEN)🚀 Starting backend on http://localhost:8000$(NC)"
	cd backend && python -m uvicorn main:app --reload

frontend:
	@echo "$(GREEN)🚀 Starting frontend on http://localhost:4200$(NC)"
	cd frontend && npm start

# ============================================================================
# TESTING & CODE QUALITY
# ============================================================================

ensure-backend-venv:
	@if [ ! -x "$(BACKEND_VENV_PY)" ]; then \
		echo "$(RED)❌ Backend virtualenv not found at backend/.venv$(NC)"; \
		echo "$(YELLOW)Create it first: cd backend && python3 -m venv .venv && source .venv/bin/activate$(NC)"; \
		echo "$(YELLOW)Then install deps (dev): pip install -e . pytest pytest-cov pytest-asyncio$(NC)"; \
		exit 1; \
	fi

ensure-frontend-deps:
	@if [ ! -x "frontend/node_modules/.bin/ng" ]; then \
		echo "$(YELLOW)⚠️  Frontend dependencies not found. Installing with npm ci...$(NC)"; \
		cd frontend && npm ci; \
	fi

test: ensure-backend-venv backend-test-unit backend-test-integration frontend-test
	@echo "$(GREEN)✅ All tests completed!$(NC)"

backend-test: ensure-backend-venv backend-test-unit backend-test-integration
	@echo "$(GREEN)✅ All backend tests passed!$(NC)"

backend-test-unit: ensure-backend-venv
	@echo "$(GREEN)🧪 Running backend unit tests (no DB)...$(NC)"
	cd backend && .venv/bin/python -m pytest -c pytest.ini tests/unit -m unit -v --tb=short --cov=app --cov-report=html
	@echo "$(GREEN)✅ Unit tests passed!$(NC)"
	@echo "$(BLUE)Coverage report: backend/htmlcov/index.html$(NC)"

backend-test-integration: ensure-backend-venv
	@echo "$(GREEN)🧪 Running backend integration tests (with real DB)...$(NC)"
	cd backend && .venv/bin/python -m pytest -c pytest.ini tests/integration -m integration -v --tb=short
	@echo "$(GREEN)✅ Integration tests passed!$(NC)"

backend-test-coverage: ensure-backend-venv
	@echo "$(GREEN)🧪 Running all backend tests with coverage report...$(NC)"
	cd backend && .venv/bin/python -m pytest -c pytest.ini tests/unit tests/integration -v --tb=short --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Tests completed!$(NC)"
	@echo "$(BLUE)Coverage report: backend/htmlcov/index.html$(NC)"

frontend-test: ensure-frontend-deps
	@echo "$(GREEN)🧪 Running frontend tests...$(NC)"
	cd frontend && npm exec -- ng test --watch=false --code-coverage
	@echo "$(GREEN)✅ Frontend tests passed!$(NC)"

backend-validate-tests: ensure-backend-venv
	@echo "$(GREEN)✓ Validating test configuration...$(NC)"
	cd backend && .venv/bin/python validate_tests.py
	@echo "$(GREEN)✅ Test configuration valid!$(NC)"

lint:
	@echo "$(GREEN)🔍 Running linters...$(NC)"
	cd backend && poetry run ruff check app/ --output-format=github
	cd backend && poetry run ruff format app/ --check
	cd frontend && npm run lint
	cd frontend && npm run type-check
	@echo "$(GREEN)✅ Linting complete!$(NC)"

frontend-build:
	@echo "$(GREEN)🔨 Running TypeScript type-check and production build...$(NC)"
	cd frontend && npm run type-check
	cd frontend && npm run build
	@echo "$(GREEN)✅ Frontend build complete!$(NC)"


# ============================================================================
# DOCKER BUILD & PUSH
# ============================================================================

docker-build:
	@if [ -z "$(ENV)" ]; then echo "$(RED)❌ ENV not set. Usage: make docker-build ENV=staging$(NC)"; exit 1; fi
	@echo "$(GREEN)🔨 Building Docker images for ENV=$(ENV) (platform=$(DOCKER_PLATFORM))...$(NC)"
	docker buildx build --platform $(DOCKER_PLATFORM) --provenance=false --sbom=false --build-arg BUILD_ENV=$(ENV) -t mypythonproject1/backend:$(ENV) --load ./backend
	docker buildx build --platform $(DOCKER_PLATFORM) --provenance=false --sbom=false --build-arg BUILD_ENV=$(ENV) -t mypythonproject1/frontend:$(ENV) --load ./frontend
	@echo "$(GREEN)✅ Docker images built$(NC)"

docker-push:
	@if [ -z "$(ENV)" ]; then echo "$(RED)❌ ENV not set. Usage: make docker-push ENV=staging$(NC)"; exit 1; fi
	@if [ -z "$(AWS_ACCOUNT_ID)" ]; then echo "$(RED)❌ Unable to detect AWS_ACCOUNT_ID — check AWS credentials$(NC)"; exit 1; fi
	@echo "$(GREEN)📤 Pushing Docker images to ECR for ENV=$(ENV)...$(NC)"
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker tag mypythonproject1/backend:$(ENV) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/mypythonproject1/backend:$(ENV)
	docker tag mypythonproject1/frontend:$(ENV) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/mypythonproject1/frontend:$(ENV)
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/mypythonproject1/backend:$(ENV)
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/mypythonproject1/frontend:$(ENV)
	@echo "$(GREEN)✅ Images pushed to ECR$(NC)"

# ============================================================================
# CLEANUP
# ============================================================================

clean:
	@echo "$(YELLOW)🧹 Cleaning build artifacts...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name build -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .angular -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

.DEFAULT_GOAL := help