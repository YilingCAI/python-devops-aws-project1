# Environment Configuration Guide

How local, staging, and production environments are configured and promoted.

## Environment types

- Local: `config/.env.dev` copied to `deploy/.env`
- Staging: `../mypythonproject1-infra/environments/staging/terraform.tfvars` + GitHub Environment `staging`
- Production: `../mypythonproject1-infra/environments/prod/terraform.tfvars` + GitHub Environment `production`

## Local development

```bash
cp config/.env.dev deploy/.env
docker compose -f deploy/docker-compose.yml up --build
```

Health checks:

```bash
curl http://localhost:8000/health
open http://localhost:4200
```

## Staging setup

1. Configure `../mypythonproject1-infra/environments/staging/terraform.tfvars`
2. Configure GitHub Environment `staging` secrets:
   - `AWS_ROLE_TO_ASSUME`
   - `TERRAFORM_STATE_BUCKET`
   - `TERRAFORM_LOCK_TABLE` (compatibility input; lockfile backend is active)
   - `JWT_SECRET_KEY`
3. Ensure `config/.env.staging` includes non-secret values:
   - `AWS_REGION`
   - `TF_VERSION`
4. Set Environment variable `APP_URL` for smoke tests

Deploy flow:

- Automatic on successful CI run for `develop`
- Or manual via `staging.yml` workflow dispatch

## Production setup

1. Configure `../mypythonproject1-infra/environments/prod/terraform.tfvars`
2. Configure GitHub Environment `production` secrets:
   - `AWS_ROLE_TO_ASSUME`
   - `AWS_REGION`
   - `TF_VERSION`
   - `TERRAFORM_STATE_BUCKET`
   - `TERRAFORM_LOCK_TABLE` (compatibility input; lockfile backend is active)
   - `JWT_SECRET_KEY`
3. Set Environment variable `APP_URL`
4. Enable required reviewers/approval in GitHub Environment protection rules

Deploy flow:

- Successful CI on `main` runs semantic-release
- Release tag `v*` triggers production apply/deploy/smoke-test flow

## Terraform backend behavior

Active backend locking strategy:

```bash
terraform init \
  -backend-config="bucket=<state-bucket>" \
  -backend-config="key=<env>/terraform.tfstate" \
  -backend-config="region=<region>" \
  -backend-config="use_lockfile=true"
```

`dynamodb_table` is deprecated and should not be used for new setup.

## Manual infrastructure commands

```bash
make tf-validate ENV=staging
make tf-plan ENV=staging
make tf-apply ENV=staging
```

## Pre-deploy checklist

- Tests pass (`make test`)
- Lint passes (`make lint`)
- Required GitHub Environment secrets and vars are present
- Terraform plan reviewed for target environment
