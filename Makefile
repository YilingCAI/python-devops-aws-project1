.PHONY: help install dev docker-up docker-down docker-logs \
	test backend-test frontend-test lint format clean \
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
	@echo "  $(YELLOW)make frontend-test$(NC)        - Frontend tests"
	@echo "  $(YELLOW)make lint$(NC)                 - Run linters (ruff, eslint)"
	@echo "  $(YELLOW)make format$(NC)               - Format code (black, prettier)"
	@echo ""
	@echo "$(GREEN)🏗️  TERRAFORM$(NC)"
	@echo "  $(YELLOW)make tf-validate$(NC)          - Validate Terraform"
	@echo "  $(YELLOW)make tf-plan$(NC)              - Plan infrastructure (ENV=staging|prod)"
	@echo "  $(YELLOW)make tf-apply$(NC)             - Apply infrastructure (ENV=staging|prod)"
	@echo "  $(YELLOW)make tf-destroy$(NC)           - Destroy infrastructure (ENV=staging|prod)"
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
	cd deploy && docker-compose up -d
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
	cd deploy && docker-compose down
	@echo "$(GREEN)✅ Services stopped$(NC)"

docker-restart:
	@echo "$(YELLOW)🔄 Restarting Docker Compose services...$(NC)"
	cd deploy && docker-compose restart
	@echo "$(GREEN)✅ Services restarted$(NC)"

docker-logs:
	cd deploy && docker-compose logs -f

docker-logs-backend:
	cd deploy && docker-compose logs -f backend

docker-logs-frontend:
	cd deploy && docker-compose logs -f frontend

docker-logs-db:
	cd deploy && docker-compose logs -f db

docker-clean:
	@echo "$(RED)🧹 Removing Docker Compose volumes and containers...$(NC)"
	cd deploy && docker-compose down -v
	@echo "$(GREEN)✅ Cleaned$(NC)"

docker-ps:
	@echo "$(BLUE)Docker Compose Services:$(NC)"
	cd deploy && docker-compose ps

# ============================================================================
# LOCAL DEVELOPMENT (Without Docker)
# ============================================================================

install:
	@echo "$(GREEN)📦 Installing dependencies...$(NC)"
	cd backend && pip install -e . && cd ..
	cd frontend && npm install && cd ..
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

test: backend-test-unit backend-test-integration frontend-test
	@echo "$(GREEN)✅ All tests completed!$(NC)"

backend-test: backend-test-unit backend-test-integration
	@echo "$(GREEN)✅ All backend tests passed!$(NC)"

backend-test-unit:
	@echo "$(GREEN)🧪 Running backend unit tests (no DB)...$(NC)"
	cd backend && python -m pytest tests/unit -m unit -v --tb=short --cov=app --cov-report=html
	@echo "$(GREEN)✅ Unit tests passed!$(NC)"
	@echo "$(BLUE)Coverage report: backend/htmlcov/index.html$(NC)"

backend-test-integration:
	@echo "$(GREEN)🧪 Running backend integration tests (with real DB)...$(NC)"
	cd backend && python -m pytest tests/integration -m integration -v --tb=short
	@echo "$(GREEN)✅ Integration tests passed!$(NC)"

backend-test-coverage:
	@echo "$(GREEN)🧪 Running all backend tests with coverage report...$(NC)"
	cd backend && python -m pytest tests/unit tests/integration -v --tb=short --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Tests completed!$(NC)"
	@echo "$(BLUE)Coverage report: backend/htmlcov/index.html$(NC)"

frontend-test:
	@echo "$(GREEN)🧪 Running frontend tests...$(NC)"
	cd frontend && npm run test -- --watch=false --coverage
	@echo "$(GREEN)✅ Frontend tests passed!$(NC)"

backend-validate-tests:
	@echo "$(GREEN)✓ Validating test configuration...$(NC)"
	cd backend && python validate_tests.py
	@echo "$(GREEN)✅ Test configuration valid!$(NC)"

lint:
	@echo "$(GREEN)🔍 Running linters...$(NC)"
	cd backend && ruff check app/ --output-format=github
	cd frontend && npm run lint
	@echo "$(GREEN)✅ Linting complete!$(NC)"

format:
	@echo "$(GREEN)✨ Formatting code...$(NC)"
	cd backend && black app/ && ruff check app/ --fix
	cd frontend && npm run format
	@echo "$(GREEN)✅ Code formatted!$(NC)"

# ============================================================================
# TERRAFORM OPERATIONS
# ============================================================================

tf-validate:
	@echo "$(GREEN)📋 Validating Terraform...$(NC)"
	@bash scripts/terraform-validate.sh

tf-plan:
	@if [ -z "$(ENV)" ]; then echo "$(RED)❌ ENV not set. Usage: make tf-plan ENV=staging$(NC)"; exit 1; fi
	@echo "$(GREEN)📋 Planning Terraform for ENV=$(ENV)...$(NC)"
	@bash scripts/terraform-plan.sh

tf-apply:
	@if [ -z "$(ENV)" ]; then echo "$(RED)❌ ENV not set. Usage: make tf-apply ENV=staging$(NC)"; exit 1; fi
	@echo "$(GREEN)🚀 Applying Terraform for ENV=$(ENV)...$(NC)"
	@bash scripts/terraform-apply.sh

tf-destroy:
	@if [ -z "$(ENV)" ]; then echo "$(RED)❌ ENV not set. Usage: make tf-destroy ENV=staging$(NC)"; exit 1; fi
	@echo "$(RED)⚠️  Destroying Terraform infrastructure for ENV=$(ENV)...$(NC)"
	@bash scripts/terraform-destroy.sh

# ============================================================================
# DOCKER BUILD & PUSH
# ============================================================================

docker-build:
	@if [ -z "$(ENV)" ]; then echo "$(RED)❌ ENV not set. Usage: make docker-build ENV=staging$(NC)"; exit 1; fi
	@echo "$(GREEN)🔨 Building Docker images for ENV=$(ENV)...$(NC)"
	@bash scripts/docker-build.sh

docker-push:
	@if [ -z "$(ENV)" ]; then echo "$(RED)❌ ENV not set. Usage: make docker-push ENV=staging$(NC)"; exit 1; fi
	@echo "$(GREEN)📤 Pushing Docker images for ENV=$(ENV)...$(NC)"
	@bash scripts/docker-build.sh push

# ============================================================================
# ECS DEPLOYMENT
# ============================================================================

ecs-deploy:
	@if [ -z "$(ENV)" ] || [ -z "$(IMAGE_TAG)" ]; then \
		echo "$(RED)❌ Missing parameters. Usage: make ecs-deploy ENV=staging IMAGE_TAG=sha-abc123$(NC)"; exit 1; fi
	@echo "$(GREEN)🚀 Deploying to ECS (ENV=$(ENV), IMAGE_TAG=$(IMAGE_TAG))...$(NC)"
	@bash scripts/ecs-deploy.sh

# ============================================================================
# FULL DEPLOYMENT ORCHESTRATION
# ============================================================================

deploy:
	@if [ -z "$(ENV)" ] || [ -z "$(IMAGE_TAG)" ]; then \
		echo "$(RED)❌ Missing parameters. Usage: make deploy ENV=staging IMAGE_TAG=sha-abc123$(NC)"; exit 1; fi
	@echo "$(GREEN)🚀 Full deployment starting (ENV=$(ENV), IMAGE_TAG=$(IMAGE_TAG))...$(NC)"
	@$(MAKE) docker-build ENV=$(ENV)
	@$(MAKE) docker-push ENV=$(ENV)
	@$(MAKE) ecs-deploy ENV=$(ENV) IMAGE_TAG=$(IMAGE_TAG)
	@echo "$(GREEN)✅ Deployment complete!$(NC)"

deploy-staging:
	@if [ -z "$(IMAGE_TAG)" ]; then echo "$(RED)❌ IMAGE_TAG not set. Usage: make deploy-staging IMAGE_TAG=...$(NC)"; exit 1; fi
	@echo "$(GREEN)🚀 Deploying to STAGING (ENV=staging, IMAGE_TAG=$(IMAGE_TAG))...$(NC)"
	@$(MAKE) deploy ENV=staging IMAGE_TAG=$(IMAGE_TAG)

deploy-prod:
	@if [ -z "$(IMAGE_TAG)" ]; then echo "$(RED)❌ IMAGE_TAG not set. Usage: make deploy-prod IMAGE_TAG=...$(NC)"; exit 1; fi
	@echo "$(RED)🚀 Deploying to PRODUCTION (ENV=prod, IMAGE_TAG=$(IMAGE_TAG))...$(NC)"
	@$(MAKE) deploy ENV=prod IMAGE_TAG=$(IMAGE_TAG)

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