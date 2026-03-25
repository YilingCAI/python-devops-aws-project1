# terraform_bootstrap

Local-only Terraform configuration that provisions the one-time AWS prerequisites required before any environment (`dev`, `staging`, `prod`) can be deployed.

This configuration is **not run in CI**. It is intended to be executed manually by a project administrator from a local machine using static AWS credentials.

---

## What It Provisions

| Resource | Purpose |
|---|---|
| S3 buckets (×3) | Remote Terraform state storage for dev, staging, and prod |
| S3 bucket versioning + encryption | State bucket hardening (AES-256, versioning enabled, public access blocked) |
| ECR repository — backend | Container image registry for the FastAPI backend |
| ECR repository — frontend | Container image registry for the Angular frontend |
| GitHub OIDC provider | Allows GitHub Actions to authenticate to AWS without long-lived keys |
| IAM role — GitHubActionsRole | Assumed by CI via OIDC; grants permissions for ECS, ECR, RDS, Secrets Manager, etc. |

---

## Directory Structure

```
terraform_bootstrap/
├── .aws.local.env            # Local AWS credentials (never commit — gitignored)
├── Makefile                  # Convenience targets: init, plan, apply, destroy
└── bootstrap/
    ├── main.tf               # S3, ECR, OIDC, and IAM resources
    ├── provider.tf           # AWS provider configuration
    ├── variables.tf          # Input variable definitions
    ├── outputs.tf            # Outputs: bucket names, role ARN, ECR URLs
    └── env/
        └── bootstrap.tfvars  # Variable values for this run (gitignored)
```

---

## Prerequisites

1. **AWS credentials** — An IAM user or assumed role with permissions to create S3, ECR, IAM, and OIDC resources in the target account.
2. **`.aws.local.env`** — Copy the example below, fill in your credentials, and save it to `terraform_bootstrap/.aws.local.env`. This file is gitignored and must never be committed.

```bash
# .aws.local.env — local credentials only, never commit
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
AWS_ACCOUNT_ID=<your-account-id>
AWS_ACCESS_KEY_ID=<your-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
```

3. **`bootstrap/env/bootstrap.tfvars`** — Create this file with at minimum the required variables:

```hcl
github_oidc_subjects = [
  "repo:YOUR_ORG/mypythonproject1:ref:refs/heads/main",
  "repo:YOUR_ORG/mypythonproject1-infra:ref:refs/heads/main"
]

# Optional overrides
project_name        = "mypythonproject1"
environments        = ["dev", "staging", "prod"]
expected_account_id = "<your-account-id>"
```

---

## Usage

All commands are run from the `terraform_bootstrap/` directory.

### Initialize

```bash
make bootstrap-init
```

Loads credentials from `.aws.local.env`, verifies AWS identity, and runs `terraform init` inside `bootstrap/`.

### Plan

```bash
make bootstrap-plan
```

Shows the resources that will be created without applying any changes.

### Apply

```bash
make bootstrap-apply
```

Creates all bootstrap resources. Safe to re-run — Terraform will only create what does not already exist.

### Destroy

```bash
make bootstrap-destroy
```

Removes all bootstrap resources. Use with caution — destroying state buckets will make existing environment state unrecoverable unless the S3 bucket is versioned and recoverable.

---

## Outputs

After a successful apply, Terraform prints:

| Output | Description |
|---|---|
| `state_bucket_names` | Map of environment → S3 bucket name |
| `state_bucket_arns` | Map of environment → S3 bucket ARN |
| `github_actions_role_arn` | IAM role ARN to configure in GitHub Actions secrets |
| `github_actions_role_name` | Friendly name of the shared CI role |
| `github_oidc_provider_arn` | ARN of the GitHub OIDC identity provider |
| `backend_ecr_repository_url` | ECR URL for backend image pushes |
| `frontend_ecr_repository_url` | ECR URL for frontend image pushes |

Copy the `github_actions_role_arn` value into the `AWS_ROLE_ARN` secret in each GitHub repository that runs CI/CD workflows.

---

## Security Notes

- `.aws.local.env` and `bootstrap/env/bootstrap.tfvars` are gitignored. Verify this before committing.
- OIDC subjects must be scoped to specific repositories and branches. Wildcard subjects are not recommended.
- The `expected_account_id` variable adds a Terraform-level guard to prevent accidental applies against the wrong account.
- S3 state buckets are created with versioning enabled, AES-256 encryption, and all public access blocked.

---

## Relationship to Other Repositories

Once bootstrap is applied, the outputs feed directly into the environment configurations:

- **State bucket names** → `backend.hcl` in each `environments/<env>/` root of the infra repos
- **GitHub Actions role ARN** → `AWS_ROLE_ARN` GitHub Actions secret
- **ECR URLs** → `terraform.tfvars` image URI variables in each environment root
