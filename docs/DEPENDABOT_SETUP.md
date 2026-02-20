# Dependabot Configuration - Production Setup

## Overview

This document explains the production-ready Dependabot configuration for managing dependencies across a cloud-native stack with FastAPI backend, Angular frontend, Terraform infrastructure, and GitHub Actions CI/CD.

---

## 🎯 Configuration Summary

| Ecosystem | Location | Schedule | Max PRs | Purpose |
|-----------|----------|----------|---------|---------|
| **pip (Poetry)** | `/backend` | Weekly (Mon 02:00) | 5 | Python dependencies |
| **Docker** | `/backend` | Weekly (Mon 03:30) | 2 | Backend base image |
| **Docker** | `/frontend` | Weekly (Mon 03:00) | 2 | Frontend base image |
| **Terraform** | `/infra` | Weekly (Tue 04:00) | 3 | IaC providers/modules |
| **GitHub Actions** | `/` | Weekly (Wed 02:00) | 4 | CI/CD actions |

---

## 📦 Ecosystem Details

### 1. Python Backend (Poetry)

**Configuration:**
```yaml
package-ecosystem: "pip"
directory: "/backend"
schedule: weekly (Monday 02:00 UTC)
open-pull-requests-limit: 5
```

**Key Features:**
- ✅ Ignores `pycrypto` (deprecated, requires manual migration)
- ✅ Commits prefixed with `build(backend):` and `build(backend-dev):`
- ✅ Labeled: `backend`, `dependencies`
- ✅ Security updates bypass schedule

**Why This Matters:**
- Poetry creates deterministic `poetry.lock` file
- Lock file changes trigger Docker layer cache invalidation
- Cache busting ensures fresh dependencies in container builds
- CI tests all backend updates automatically

**pycrypto Handling:**
```
Why ignored?
  • pycrypto is deprecated (no longer maintained)
  • Replacement: pycryptodome with different imports
  • Requires code changes: from Crypto → from Cryptodome
  • Should be manually reviewed and tested

Manual Update Steps:
  1. Update pyproject.toml: pycrypto → pycryptodome
  2. Run: poetry update
  3. Update imports in code: Crypto → Cryptodome
  4. Test: pytest tests/
  5. Create PR with comprehensive commit message
```

### 2. Docker Base Images

**Configuration:**
```yaml
package-ecosystem: "docker"
directories: ["/backend", "/frontend"]
schedule: weekly (Monday 03:00 & 03:30 UTC)
open-pull-requests-limit: 2 each
versioning-strategy: "semver-opt-out"
```

**Key Features:**
- ✅ Separate PRs for backend and frontend
- ✅ Conservative: Only patch/minor updates (no major breaking changes)
- ✅ Labeled: `docker`, `dependencies`
- ✅ Commits: `build(docker):`

**Why Docker Updates Matter:**

Backend (Python 3.12):
```
Base image: python:3.12-slim
Contains: OS packages + Python runtime
Risk: Unpatched OS vulnerabilities (openssl, curl, etc.)
Benefit: Security patches from Python/Debian teams
```

Frontend (Node.js 20):
```
Base image: node:20-alpine
Contains: Alpine Linux + Node.js
Risk: Unpatched Alpine packages
Benefit: Security updates + Node.js patches
```

**Multi-Stage Build Strategy:**
```dockerfile
# Stage 1: Builder (with dev dependencies)
FROM python:3.12-slim AS builder
# Install and compile packages

# Stage 2: Production (minimal)
FROM python:3.12-slim
# Copy compiled packages only
```

Benefits:
- Reduces final image size
- Isolates build tools from production
- Security: Fewer packages in production image
- Docker cache: Builder stage cached separately

### 3. Terraform Infrastructure

**Configuration:**
```yaml
package-ecosystem: "terraform"
directory: "/infra"
schedule: weekly (Tuesday 04:00 UTC)
open-pull-requests-limit: 3
```

**Key Features:**
- ✅ Allows all version types (Terraform maintains compatibility)
- ✅ Labeled: `infra`, `dependencies`, `terraform`
- ✅ Commits: `build(terraform):`
- ✅ Updates providers and modules

**Why Terraform Updates Matter:**

AWS Provider:
```
Current: aws provider ~> 5.0
Updates: Bug fixes, new resources, API changes
Risk: Missing security patches if outdated
Benefit: Latest AWS features for ECS Fargate
```

Terraform Modules:
```
Examples: alb, ecs, rds, networking modules
Updates: Security patches, performance improvements
Benefit: Best practices from HashiCorp community
```

**Important Constraints:**
- ✅ Dependabot only updates provider/module versions
- ❌ Does NOT modify Terraform code
- ❌ Does NOT change resource configurations
- ✅ CI validates all infrastructure changes

**How It Works:**
```hcl
# Original
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# After Dependabot update
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.47"  # ← Only version changes
    }
  }
}
```

### 4. GitHub Actions

**Configuration:**
```yaml
package-ecosystem: "github-actions"
directory: "/"
schedule: weekly (Wednesday 02:00 UTC)
open-pull-requests-limit: 4
```

**Key Features:**
- ✅ Updates all workflow action versions
- ✅ Labeled: `ci`, `dependencies`
- ✅ Commits: `ci:`
- ✅ Allows all version types

**Critical Actions Updated:**
```yaml
# Setup and checkout
- actions/checkout@v4          # Git checkout
- actions/setup-python@v6      # Python environment
- actions/setup-node@v4        # Node.js environment

# Docker building
- docker/setup-buildx-action@v2
- docker/build-push-action@v4

# Terraform
- hashicorp/setup-terraform@v2

# Caching
- actions/cache@v4            # GHA cache for deps

# Security scanning
- aquasecurity/trivy-action@master
- github/codeql-action/*

# Utilities
- actions/github-script@v7
```

**Why Action Updates Matter:**
- Security patches for action code
- Performance improvements
- New features and bug fixes
- Compatibility with latest runners

---

## 🔐 Security Integration

### CI/CD Pipeline

**Dependabot PR Flow:**
```
1. Dependabot creates PR with dependency update
   ↓
2. PR targets: main | staging | develop branch
   ↓
3. CI/CD pipeline automatically triggers
   ↓
4. All checks run (tests, security scans, linting)
   ↓
5. If ✅ all checks pass → Auto-merge (optional)
   ↓
6. If ❌ checks fail → Manual review required
```

**Security Scans Run:**
- ✅ Trivy filesystem scan (vulnerability detection)
- ✅ Bandit security checks (Python)
- ✅ ESLint linting (JavaScript)
- ✅ TypeScript type checking
- ✅ Python unit & integration tests
- ✅ Docker image vulnerability scan

**No Credentials Used:**
- ❌ AWS credentials NOT in Dependabot context
- ❌ Docker registry credentials NOT in PRs
- ✅ Secrets Manager stays isolated
- ✅ ECR push only on main/staging/develop

### Auto-Merge Workflow

**File:** `.github/workflows/dependabot-auto-merge.yml`

**Features:**
- ✅ Waits for all CI checks to complete
- ✅ Only merges if actor is `dependabot[bot]`
- ✅ Uses squash merge strategy
- ✅ 30-minute timeout for CI completion
- ✅ Posts comments explaining status

**Auto-Merge Strategy:**
```
Condition: All required checks PASS
    ↓
Merge Method: Squash (clean history)
    ↓
Branch Deletion: Automatic after merge
    ↓
Result: Linear git history
```

**Example Merge Commit:**
```
build(backend): upgrade poetry dependencies #123

This PR was automatically merged by Dependabot auto-merge workflow 
after all CI checks passed.
```

---

## 📅 Schedule Breakdown

### Monday
- 02:00 UTC: Poetry dependencies (Backend)
- 03:00 UTC: Docker Frontend
- 03:30 UTC: Docker Backend

### Tuesday
- 04:00 UTC: Terraform

### Wednesday
- 02:00 UTC: GitHub Actions

**Rationale:**
- Spread updates across week (avoid PR overload)
- Monday: App dependencies tested throughout week
- Tuesday: Infrastructure reviewed before weekend
- Wednesday: CI actions ready for rest of week
- Off-peak hours: Less competition for CI resources

---

## 🎯 PR Limits

| Ecosystem | Max PRs | Reason |
|-----------|---------|--------|
| Poetry | 5 | High velocity, safe updates |
| Docker | 2 | Conservative, image rebuilds expensive |
| Terraform | 3 | Moderate, requires infrastructure review |
| GitHub Actions | 4 | Medium velocity, safe to test in parallel |

**Total Maximum:** ~14 open PRs (worst case)

**Benefit:** Prevents Dependabot from overwhelming review queue

---

## 🏷️ Labeling Strategy

**Consistent Labels:**
```
backend
  → Python dependencies (Poetry)
  → Auto-merged on success

docker
  → Base image updates (Backend/Frontend)
  → Requires manual review

infra
  → Terraform updates
  → Requires infrastructure team review

ci
  → GitHub Actions
  → Auto-merged on success
```

**How Labels Help:**
- Team routing (assign to backend team, infra team, etc.)
- Filtering (find all Docker updates)
- Automation (different workflows per label)
- Metrics (track update velocity per ecosystem)

---

## ⚙️ Branch Targets

**PR Branches:**
```yaml
pull_request:
  branches: ["main", "develop", "staging"]
  types: [opened, synchronize, reopened]
```

**Strategy:**
- ✅ `main`: Production deployments, tested thoroughly
- ✅ `staging`: Pre-production environment
- ✅ `develop`: Development integration branch
- ❌ `test`: Push-only, no PR deployments

**Benefit:**
- Dependabot PRs run full CI on all deployment branches
- Staging/develop catch issues before production
- Multiple branches ensure quality gates

---

## 🚀 Deployment Flow

### Development Process
```
Dependabot PR Created → CI Tests → Auto-Merge (if enabled)
                                        ↓
                            Merged to develop
                                        ↓
                        Integration tests run
                                        ↓
                    Manual promotion to staging
                                        ↓
                        Staging deployment
                                        ↓
                    Manual promotion to main
                                        ↓
                    Production deployment
                                        ↓
                        ECS Fargate updated
```

### AWS Deployment (No CodeDeploy)
```
1. Docker image pushed to ECR (only on main/staging/develop)
2. Terraform updates ECS task definition
3. ECS auto-scaling updates service
4. Blue-green deployment (zero-downtime)
5. Health checks verify deployment
```

---

## 🔍 Monitoring & Maintenance

### Check Dependabot Status

**GitHub UI:**
1. Repository → Settings → Code security & analysis
2. Scroll to "Dependabot"
3. View: Alerts, configuration, updates

**View Recent PRs:**
```bash
# List Dependabot PRs
gh pr list --search "author:dependabot" --state all

# View specific PR details
gh pr view <PR_NUMBER>
```

### Metrics to Track
- Number of Dependabot PRs merged per week
- Percentage auto-merged vs manually reviewed
- Average time from creation to merge
- CI failure rate for Dependabot PRs

### Troubleshooting

**Problem: Dependabot not creating PRs**
- Check: Settings → Code security & analysis → Dependabot enabled
- Check: No 0-PR limit in configuration
- Check: No branch protection rules blocking PRs

**Problem: CI not running on Dependabot PRs**
- Check: PR targets main/staging/develop
- Check: CI workflow has `pull_request` trigger
- Check: No branch protection requiring manual approval

**Problem: Auto-merge not working**
- Check: `.github/workflows/dependabot-auto-merge.yml` exists
- Check: CI must pass before merge
- Check: No required review approvals blocking merge

---

## 💡 Best Practices

### For Developers
1. ✅ Review Dependabot PRs regularly
2. ✅ Check CI logs if tests fail
3. ✅ Understand dependency updates (major/minor/patch)
4. ✅ Test locally if concerned
5. ✅ Request changes if incompatibility found

### For DevOps
1. ✅ Monitor PR merge rates weekly
2. ✅ Adjust PR limits if too many/few updates
3. ✅ Update action versions manually if critical
4. ✅ Review security alerts from scanning
5. ✅ Document any ecosystem-specific needs

### For Security
1. ✅ All security scans run on Dependabot PRs
2. ✅ No production secrets in PR context
3. ✅ Audit trail in git history
4. ✅ Two-factor authentication on GitHub
5. ✅ Branch protection rules in place

---

## 📚 Related Files

**Core Configuration:**
- `.github/dependabot.yml` - Dependabot settings
- `.github/workflows/ci.yml` - CI/CD pipeline
- `.github/workflows/dependabot-auto-merge.yml` - Auto-merge workflow

**Dependency Files:**
- `backend/pyproject.toml` - Python dependencies
- `backend/poetry.lock` - Python lock file
- `backend/Dockerfile` - Backend image
- `frontend/package.json` - JavaScript dependencies
- `frontend/package-lock.json` - JavaScript lock file
- `frontend/Dockerfile` - Frontend image
- `infra/main.tf` - Terraform configuration
- `infra/.terraform.lock.hcl` - Terraform lock file

---

## 🔗 External Resources

- [GitHub Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Dependabot Configuration Options](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-dependency-updates)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)

---

## ✨ Summary

This Dependabot configuration provides:

✅ **Automated Updates**
- Python, Docker, Terraform, GitHub Actions
- Weekly scheduled updates
- Immediate security patches

✅ **Quality Assurance**
- Full CI/CD runs on all PRs
- Security scanning before merge
- Manual review option for complex changes

✅ **Operational Efficiency**
- Auto-merge for safe updates
- Reduced manual work
- Clean git history (squash merge)

✅ **Safety**
- No production credentials exposed
- Isolated test environment
- Approval workflows maintained

**Status:** Production-ready ✨
