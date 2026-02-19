# MyPythonProject1 - Full-Stack DevOps Platform

A production-ready full-stack application with unified DevOps infrastructure, comprehensive testing, and enterprise-grade deployment pipelines.

## 📋 Project Overview

This monorepo contains:
- **Backend**: Python FastAPI microservices with PostgreSQL
- **Frontend**: Angular SPA with TypeScript
- **Infrastructure**: AWS (ECS, Fargate, ALB, RDS) via Terraform
- **CI/CD**: GitHub Actions with environment-based deployments
- **DevOps**: Unified Makefile CLI for local and CI/CD workflows

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
make install

# Run locally (backend + frontend)
make dev

# Run tests
make test

# Lint and format code
make lint
make format
```

### Infrastructure (Terraform)
```bash
# Validate infrastructure
make tf-validate ENV=staging

# Plan changes (review first!)
make tf-plan ENV=staging

# Apply changes
make tf-apply ENV=staging
```

### Deployment
```bash
# Build and push Docker images
make docker-build ENV=staging IMAGE_TAG=v1.0.0

# Full deployment (terraform + docker + ECS)
make deploy ENV=staging IMAGE_TAG=v1.0.0
```

## 📁 Folder Structure

```
├── README.md                    # This file - project overview
├── Makefile                     # Unified CLI for all operations
├── LICENSE                      # Project license
│
├── backend/                     # FastAPI microservices
│   ├── README.md               # Backend setup & API documentation
│   ├── main.py                 # Application entry point
│   ├── app/                    # Application code
│   ├── tests/                  # Backend unit tests
│   ├── alembic/                # Database migrations
│   └── pyproject.toml          # Python dependencies
│
├── frontend/                    # Angular SPA
│   ├── README.md               # Frontend setup & guidelines
│   ├── src/                    # Angular source code
│   ├── package.json            # Node dependencies
│   ├── tsconfig.json           # TypeScript configuration
│   └── angular.json            # Angular CLI configuration
│

## 🔐 Security & Secrets Management

### Principle: **Secrets in Code = Never**

All environment configuration is centralized in `config/` folder:

**Tracked in Git (✅):**
- `config/.env.*.example` - Templates for each environment
- `.gitignore` - Security rules

**Never in Git (❌):**
- `config/.env.dev` - Development settings
- `config/.env.test` - Testing settings
- `config/.env.local` - Local overrides
- `config/.env.prod` - Production settings

**For CI/CD:**
- GitHub Secrets stored in repository settings
- Used via `${{ secrets.SECRET_NAME }}` in workflows
- OIDC token for AWS authentication (no hardcoded credentials)

**For Runtime:**
- AWS Secrets Manager for sensitive data
- ECS task definitions inject secrets as environment variables
- Application reads from environment at runtime

See [docs/ENVIRONMENT_CONFIGURATION.md](docs/ENVIRONMENT_CONFIGURATION.md) for complete setup guide.

**For CI/CD:**
- GitHub Secrets stored in repository settings (AWS_ROLE_TO_ASSUME, DB passwords, etc.)
- Used via `${{ secrets.SECRET_NAME }}` in workflows
- OIDC token for AWS authentication (no hardcoded credentials)

**For Runtime:**
- AWS Secrets Manager for sensitive data
- ECS task definitions inject secrets as environment variables
- Application reads from environment at runtime
- Terraform manages secrets creation in AWS

**For Local Development:**
- Copy `config/.env.dev.example` to `config/.env.dev`
- Copy `config/.env.test.example` to `config/.env.test`
- Optional: `config/.env.local` for local overrides
- All .env files in `config/` are git-ignored (never committed)

See [docs/SECRETS_MANAGEMENT.md](docs/SECRETS_MANAGEMENT.md) for detailed patterns and [docs/ENVIRONMENT_CONFIGURATION.md](docs/ENVIRONMENT_CONFIGURATION.md) for environment file structure.

## 🧪 Testing Strategy

### Backend Testing

#### Layer-Based Test Architecture
Tests are organized into two layers:
- **Unit Tests** (mocked, no database): Fast validation of business logic (~5 seconds)
- **Integration Tests** (real database, auto-rollback): End-to-end flow validation (~15-30 seconds)

#### Quick Local Testing
```bash
# Run unit tests only (mocked, no DB access)
make backend-test-unit

# Run integration tests only (full DB operations)
make backend-test-integration

# Run all tests with coverage report
make backend-test-coverage

# Run all tests
make backend-test
```

#### Using Helper Scripts
```bash
# Run unit tests
bash scripts/run-tests.sh unit

# Run integration tests
bash scripts/run-tests.sh integration

# Run all tests (unit + integration)
bash scripts/run-tests.sh all

# Generate coverage HTML report
bash scripts/run-tests.sh coverage
```

#### Database Setup (Local Development)
```bash
# Setup test database for local development
bash scripts/setup-test-db.sh local

# Or in Docker environment
bash scripts/setup-test-db.sh docker
```

#### Coverage Reports
```bash
# HTML coverage report
make backend-test-coverage

# View report
open htmlcov/index.html
```

#### Test Configuration Files
- `.env.test`: Test environment variables (DB URL, secrets)
- `pytest.ini`: Pytest configuration with `asyncio_mode=auto` and markers
- `tests/validate_tests.py`: Configuration validator script

#### Key Features
- ✅ Automatic database transaction rollback between tests (no data pollution)
- ✅ AsyncClient for testing async endpoints
- ✅ Fixture-based dependency injection (database, HTTP client, auth)
- ✅ Pre-created test users and JWT tokens
- ✅ No database mocking in integration tests (real DB with rollback)
- ✅ No router testing in unit tests (only business logic)

See [Backend Testing Guide](docs/INFRASTRUCTURE_ADAPTATION_SUMMARY.md) for detailed documentation.

### Frontend
```bash
# Unit and integration tests
cd frontend && npm test

# E2E tests
npm run e2e
```

### Infrastructure
```bash
# Terraform validation (runs in CI/CD)
terraform validate

# Static analysis with Checkov
checkov -d infra/

# Plan review before apply
make tf-plan ENV=staging
```

## 🚀 Deployment Environments

| Environment | Access | Approval | Changes |
|-------------|--------|----------|---------|
| **dev** | Developers | None | Immediate |
| **staging** | DevOps Team | Optional | Before prod testing |
| **prod** | DevOps Lead | Required | Manual approval |

### Deploying to Each Environment

```bash
# Staging - no approval needed
make deploy ENV=staging IMAGE_TAG=sha-abc123

# Production - requires manual approval in GitHub Actions
make deploy-prod IMAGE_TAG=v1.2.3
```

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Code: backend/, frontend/, infra/, scripts/, docs/ │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼─────┐       ┌──────▼────┐
   │ GitHub   │       │ Branch    │
   │ Actions  │       │ Push      │
   │ Triggered│       │ Triggered │
   └────┬─────┘       └──────┬────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  GitHub Actions     │
        │  Workflow           │
        ├─────────────────────┤
        │ 1. Validate inputs  │
        │ 2. Terraform plan   │
        │ 3. Approval gate    │
        │ 4. Terraform apply  │
        │ 5. Docker build     │
        │ 6. ECS deploy       │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  AWS Services       │
        ├─────────────────────┤
        │ • S3 (state)        │
        │ • DynamoDB (locks)  │
        │ • ECR (images)      │
        │ • ECS (containers)  │
        │ • RDS (database)    │
        │ • ALB (load balancer)
        │ • Secrets Manager   │
        └─────────────────────┘
```

## 🛠️ Common Tasks

### Adding a New Feature
1. Create feature branch: `git checkout -b feature/my-feature`
2. Develop and test locally: `make dev`
3. Run tests: `make test`
4. Format code: `make format`
5. Push and open PR
6. Once merged to develop → automatic staging deployment

### Deploying to Production
1. Ensure all tests pass
2. Merge to main branch
3. Create release tag: `git tag -a v1.2.3`
4. GitHub Actions deploys to prod with approval
5. Verify in AWS console

### Rolling Back
```bash
# List previous images
aws ecr describe-images --repository-name myapp-backend

# Deploy previous version
make deploy ENV=prod IMAGE_TAG=v1.2.2
```

### Debugging Terraform
```bash
# See what changed
make tf-plan ENV=staging

# Check current state
cd infra && terraform show

# Destroy specific resource (dangerous!)
cd infra && terraform destroy -target='aws_ecs_service.backend'
```

## 📖 Documentation

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and component overview
- **[docs/ONBOARDING.md](docs/ONBOARDING.md)** - Setup guide for new team members
- **[docs/SECRETS_MANAGEMENT.md](docs/SECRETS_MANAGEMENT.md)** - How secrets are secured
- **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Detailed deployment procedures
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and fixes
- **[docs/MAKE_REFERENCE.md](docs/MAKE_REFERENCE.md)** - All Makefile targets explained
- **[backend/README.md](backend/README.md)** - Backend setup and API docs
- **[frontend/README.md](frontend/README.md)** - Frontend setup and guidelines
- **[infra/README.md](infra/README.md)** - Infrastructure and Terraform docs

## 🤝 Contributing

1. Fork or branch from `develop`
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and test: `make test`
4. Format code: `make format`
5. Commit with clear message
6. Push and create Pull Request
7. Ensure CI passes and get review approval
8. Merge to develop (staging auto-deploys)

## 📝 Makefile Quick Reference

```bash
# Development
make help                  # Show all targets
make install              # Install dependencies
make dev                  # Run locally
make test                 # Run all tests
make lint                 # Lint code
make format               # Format code

# Infrastructure
make tf-validate ENV=staging
make tf-plan ENV=staging
make tf-apply ENV=staging
make tf-destroy ENV=staging  # ⚠️ Dangerous!

# Deployment
make docker-build ENV=staging IMAGE_TAG=v1.0.0
make ecs-deploy ENV=staging IMAGE_TAG=v1.0.0
make deploy ENV=staging IMAGE_TAG=v1.0.0

# Cleanup
make clean                # Remove build artifacts
make clean-env            # Remove .env files
```

See [docs/MAKE_REFERENCE.md](docs/MAKE_REFERENCE.md) for complete reference.

## 🔗 External Resources

- [AWS Documentation](https://docs.aws.amazon.com/)
- [Terraform Documentation](https://www.terraform.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Angular Documentation](https://angular.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions/)

## 📞 Support

- **Issues**: Create GitHub issue with details
- **Questions**: Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Security**: See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

## 📄 License

See [LICENSE](LICENSE) file for details.

---

**Last Updated**: February 2026  
**Maintained By**: DevOps Team  
**Version**: 2.0 (Complete DevOps Refactoring)

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
lsof -i :8000
kill -9 <PID>
# Or use different port:
uvicorn app.main:app --port 8001
```

**Database connection errors:**
- Ensure PostgreSQL is running
- Check DATABASE_URL environment variable
- Run `alembic upgrade head`

### Frontend Issues

**Port 4200 already in use:**
```bash
ng serve --port 4300
```

**API connection errors:**
- Ensure backend is running on port 8000
- Check `environment.ts` for correct API URL
- Verify CORS settings on backend

**Build errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules dist
npm install
npm run build
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

See [LICENSE](./LICENSE) file for details.

## Contact & Support

For issues, questions, or contributions, please open an issue in the repository.

## Recent Updates

### Frontend Migration to Angular 19 (Latest) ⭐
- ✅ Migrated from React/Next.js to Angular 19
- ✅ Implemented standalone components
- ✅ Created services for API, Auth, and Game logic
- ✅ Added HTTP interceptors for auth and error handling
- ✅ Configured routing with protection guards
- ✅ Set up Tailwind CSS styling with components
- ✅ Updated Docker configuration
- ✅ Enhanced type safety throughout

### Backend & Infrastructure
- ✅ FastAPI backend with async support
- ✅ PostgreSQL database with migrations
- ✅ JWT authentication
- ✅ Docker containerization
- ✅ Terraform infrastructure code
- ✅ CI/CD pipeline configuration
