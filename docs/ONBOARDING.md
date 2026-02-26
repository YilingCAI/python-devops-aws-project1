# Onboarding — New Developer Guide

Everything you need to go from zero to a running local environment and your first merged PR. Estimated time: **30–45 minutes**.

---

## Prerequisites

Install these tools before starting:

### macOS
```bash
# Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# All required tools
brew install git python@3.12 node terraform awscli
brew install --cask docker

# Open Docker Desktop before continuing
open /Applications/Docker.app
```

### Ubuntu / Debian
```bash
sudo apt-get update && sudo apt-get install -y \
  git python3.12 python3-venv nodejs npm \
  docker.io docker-compose

# Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor \
  | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install terraform

# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip awscliv2.zip && sudo ./aws/install
```

### Verify versions
```bash
git --version           # 2.40+
python3 --version       # 3.12+
node --version          # 20+
docker --version        # 24+
terraform --version     # 1.5+
aws --version           # 2.x
```

---

## Step 1 — Clone & install

```bash
git clone https://github.com/your-org/mypythonproject1.git
cd mypythonproject1

# Install all dependencies at once
make install
```

`make install` installs:
- Backend Python deps via Poetry (`backend/`)
- Frontend Node deps via npm (`frontend/`)
- Root CI tooling (commitlint + semantic-release)

---

## Step 2 — Configure local environment

```bash
cp config/.env.dev deploy/.env
```

`config/.env.dev` has all non-secret local-dev settings pre-configured (local Postgres host, debug=true, test JWT key). You do not need to add any secrets to run the app locally.

---

## Step 3 — Start the full stack

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Wait for all containers to be healthy, then open:

| URL | What |
|---|---|
| http://localhost:4200 | Angular frontend |
| http://localhost:8000/docs | FastAPI OpenAPI docs |
| http://localhost:8000/health | Health check (`{"status":"ok"}`) |

### Run database migrations
```bash
docker compose -f deploy/docker-compose.yml exec backend \
  alembic upgrade head
```

---

## Step 4 — Run tests

```bash
# All tests
make test

# Backend only — unit tests (fast, no DB required)
cd backend && poetry run pytest tests/unit -m unit -v

# Backend — integration tests (needs postgres running)
cd backend && poetry run pytest tests/integration -m integration -v

# Frontend
cd frontend && npm test
```

---

## Step 5 — Understand the branch strategy

```
main         ← production-ready code only; never commit directly
  └─ develop ← integration branch; merge feature branches here
       └─ feature/your-feature ← your working branch
```

**Always branch from `develop`:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature
```

---

## Step 6 — Write code & commit

Commits **must** follow [Conventional Commits](https://www.conventionalcommits.org/). This is enforced by `commitlint` on every PR.

```bash
# Format: <type>(<optional scope>): <description>

git commit -m "feat(game): add multiplayer room endpoints"
git commit -m "fix(auth): refresh token not invalidated on logout"
git commit -m "test: add user registration integration test"
git commit -m "docs: update local setup instructions"
```

**Valid types:** `feat`, `fix`, `perf`, `refactor`, `revert`, `docs`, `style`, `test`, `build`, `ci`, `chore`

If your commit fails commitlint, you'll see an error like:
```
⧗  input: WIP: some stuff
✖  subject may not be empty [subject-empty]
✖  type may not be empty [type-empty]
```

Fix it with `git commit --amend -m "fix(auth): correct typo in error message"`.

---

## Step 7 — Open a Pull Request → develop

```bash
git push origin feature/my-new-feature
# Open PR on GitHub targeting the develop branch
```

The CI pipeline (`ci.yml`) runs automatically. All jobs must pass before merging:

| Check | Description |
|---|---|
| Commitlint | All commits in the PR follow Conventional Commits |
| Backend CI | Lint (ruff) + unit + integration tests |
| Frontend CI | ESLint + TypeScript + build |
| Security Scan | Trivy + GitGuardian |
| Dependency Audit | Snyk |
| Terraform Plan | Shows infra diff on PR (if `infra/` changed) |
| Quality Gate | Single required check summarising all above |

---

## Step 8 — After merge to develop

Your changes automatically deploy to **staging** via `staging.yml`:

1. Docker images built and pushed to GHCR
2. Terraform applies any infra changes to staging
3. ECS rolls out new containers
4. Smoke test hits `/health` — if it fails, the deploy is marked failed

Check the deployment at:
```
https://github.com/your-org/mypythonproject1/actions/workflows/staging.yml
```

Staging URL: configured in `config/.env.staging` → `APP_URL`.

---

## Common Commands Cheatsheet

```bash
# Start everything locally
make dev

# Run all tests
make test

# Lint code
make lint

# Format code
make format

# Run only backend
make backend

# Run only frontend
make frontend

# View all make targets
make help
```

---

## Troubleshooting

### `make install` fails on poetry
```bash
pip install --upgrade pip
pip install poetry
poetry --version
```

### Docker compose postgres fails to start
```bash
# Check if port 5432 is already in use
lsof -i :5432
# Kill the conflicting process or change DATABASE_PORT in deploy/.env
```

### `alembic upgrade head` — "can't connect to postgres"
Make sure the postgres container is running:
```bash
docker compose -f deploy/docker-compose.yml ps
```

### Frontend — `npm ci` fails
```bash
# Clear cache and retry
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Commitlint fails on push
Edit the failing commit:
```bash
git commit --amend -m "fix(scope): proper conventional commit message"
```
Or use interactive rebase to fix multiple commits:
```bash
git rebase -i HEAD~3
```

---

## Getting Help

- Architecture overview: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- Test strategy: [docs/TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md)
- Infrastructure details: [infra/README.md](../infra/README.md)
- Backend API: [backend/README.md](../backend/README.md)
- Frontend: [frontend/README.md](../frontend/README.md)
