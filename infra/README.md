# Infrastructure

Terraform infrastructure-as-code for AWS. Provisions VPC, ECS Fargate, RDS PostgreSQL, ALB, IAM, and ECR. Supports staging and production environments from the same codebase.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Prerequisites](#prerequisites)
3. [First-Time Bootstrap](#first-time-bootstrap)
4. [Module Reference](#module-reference)
5. [Environment Configuration](#environment-configuration)
6. [Remote State](#remote-state)
7. [Local Usage](#local-usage)
8. [CI/CD Usage](#cicd-usage)
9. [Security Model](#security-model)
10. [Outputs & Connecting Services](#outputs--connecting-services)

---

## Architecture

```
AWS Account
│
├── IAM
│   ├── GitHub OIDC Provider           ← no static keys in CI
│   ├── role/github-staging            ← used by staging.yml
│   └── role/github-production         ← used by release.yml
│
├── S3: myproject-terraform-state      ← Terraform remote state (versioned, encrypted)
├── DynamoDB: terraform-locks          ← State lock table
│
└── VPC: 10.0.0.0/16
    │
    ├── Public Subnets (10.0.101.0/24, 10.0.102.0/24) — 2 AZs
    │   ├── ALB (internet-facing, :443 HTTPS / :80 → redirect)
    │   └── NAT Gateway
    │
    ├── Private Subnets (10.0.1.0/24, 10.0.2.0/24) — 2 AZs
    │   └── ECS Fargate Cluster
    │       ├── backend service   (FastAPI :8000)
    │       └── frontend service  (Nginx :80)
    │
    └── DB Subnets (10.0.201.0/24, 10.0.202.0/24) — 2 AZs
        └── RDS PostgreSQL 16 (Multi-AZ in production)
```

---

## Prerequisites

- Terraform 1.5+
- AWS CLI v2 configured (`aws configure`)
- AWS account with permissions to create VPC, ECS, RDS, IAM, ALB, S3, DynamoDB
- Terraform state S3 bucket already created (see [First-Time Bootstrap](#first-time-bootstrap))

---

## First-Time Bootstrap

Run these commands **once per AWS account** before any `terraform apply`.

### 1. Create the S3 state bucket

```bash
BUCKET_NAME="myproject-terraform-state"
REGION="us-east-1"

aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION"

# Enable versioning (required for state history)
aws s3api put-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Block all public access
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2. Create DynamoDB lock table

```bash
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 3. Create GitHub OIDC provider (once per account)

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 4. Create IAM roles for GitHub Actions

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
GITHUB_ORG="your-org"
REPO="mypythonproject1"

# Trust policy — allows GitHub Actions to assume this role via OIDC
cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:${GITHUB_ORG}/${REPO}:environment:staging"
      }
    }
  }]
}
EOF

aws iam create-role \
  --role-name github-staging \
  --assume-role-policy-document file:///tmp/trust-policy.json

# Attach permissions (adjust to minimum required)
aws iam attach-role-policy \
  --role-name github-staging \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Repeat for production role with environment:production condition
```

---

## Module Reference

```
infra/
├── main.tf           ← Wires all modules together, S3 backend config
├── variables.tf      ← Input variables with types and validation
├── outputs.tf        ← Exports for cross-module references (ALB URL, cluster name, etc.)
├── providers.tf      ← AWS provider, required versions
│
├── modules/
│   ├── network/      ← VPC, subnets, IGW, NAT, route tables, NACLs, security groups
│   ├── alb/          ← ALB, listeners, target groups, SSL certificate
│   ├── ecs/          ← ECS cluster, task definitions, services, IAM exec role
│   ├── rds/          ← RDS instance, subnet group, parameter group, KMS key
│   └── iam/          ← OIDC provider, CI/CD roles, ECS task execution policies
│
└── envs/
    ├── staging.tfvars     ← Staging-specific values
    └── prod.tfvars        ← Production-specific values
```

### Key variables (in `variables.tf`)

| Variable | Description | Staging example | Prod example |
|---|---|---|---|
| `environment` | `staging` or `production` | `staging` | `production` |
| `aws_region` | AWS region | `us-east-1` | `us-east-1` |
| `vpc_cidr` | VPC CIDR block | `10.0.0.0/16` | `10.0.0.0/16` |
| `db_instance_class` | RDS instance type | `db.t3.micro` | `db.r6g.large` |
| `ecs_cpu` | CPU units per Fargate task | `256` | `1024` |
| `ecs_memory` | Memory MB per Fargate task | `512` | `2048` |

---

## Environment Configuration

The same Terraform code targets both environments. Environment-specific values are in tfvars files:

### `envs/staging.tfvars`
```hcl
environment     = "staging"
aws_region      = "us-east-1"
db_instance_class = "db.t3.micro"
db_multi_az     = false
ecs_cpu         = 256
ecs_memory      = 512
```

### `envs/prod.tfvars`
```hcl
environment     = "production"
aws_region      = "us-east-1"
db_instance_class = "db.r6g.large"
db_multi_az     = true
ecs_cpu         = 1024
ecs_memory      = 2048
```

---

## Remote State

The S3 backend uses **partial configuration** — sensitive values (bucket names, keys) are injected at `terraform init` time, not stored in code.

```bash
# Standard init for local/manual use
terraform init \
  -backend-config="bucket=myproject-terraform-state" \
  -backend-config="key=staging/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=terraform-locks"
```

State files are separated by environment:
- `staging/terraform.tfstate` — staging infra
- `production/terraform.tfstate` — production infra

This prevents Terraform from accidentally applying staging plans to production.

For local development / validation without touching remote state:
```bash
terraform init -backend=false
terraform validate
terraform plan -var-file="envs/staging.tfvars"
```

---

## Local Usage

```bash
cd infra

# Initialise with remote state (staging)
terraform init \
  -backend-config="bucket=myproject-terraform-state" \
  -backend-config="key=staging/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=terraform-locks"

# Validate syntax and module references
terraform validate

# Check formatting
terraform fmt -check -recursive

# Plan changes (always review before apply)
terraform plan \
  -var-file="envs/staging.tfvars" \
  -out=tfplan

# Inspect the plan in detail
terraform show tfplan

# Apply
terraform apply tfplan

# View current state
terraform show
terraform output

# Destroy all resources (destructive — use with care)
terraform destroy -var-file="envs/staging.tfvars"
```

Or use the Makefile shortcuts from the project root:

```bash
make tf-validate ENV=staging
make tf-plan     ENV=staging
make tf-apply    ENV=staging
make tf-destroy  ENV=staging   # prompt before destroying
```

---

## CI/CD Usage

### In `ci.yml` (PR validation — read-only)

```yaml
- name: Terraform init (no remote state)
  working-directory: infra
  run: terraform init -backend=false

- name: Terraform validate
  working-directory: infra
  run: terraform validate

- name: Terraform plan (dry-run, no state)
  working-directory: infra
  run: |
    terraform plan \
      -var-file="envs/staging.tfvars" \
      -no-color 2>&1 | tee plan-output.txt
```

The plan output is automatically posted as a comment on the PR.

### In `staging.yml` (real apply)

```yaml
- name: Terraform init (remote state)
  working-directory: infra
  run: |
    terraform init \
      -backend-config="bucket=${{ secrets.TERRAFORM_STATE_BUCKET }}" \
      -backend-config="key=staging/terraform.tfstate" \
      -backend-config="region=${{ env.AWS_REGION }}" \
      -backend-config="dynamodb_table=${{ secrets.TERRAFORM_LOCK_TABLE }}"

- name: Terraform apply
  working-directory: infra
  run: |
    terraform plan -var-file="envs/staging.tfvars" -out=tfplan.staging
    terraform apply -auto-approve tfplan.staging
```

Production apply in `release.yml` is identical but uses `envs/prod.tfvars` and `key=production/terraform.tfstate`, and is gated by a **manual approval** via GitHub Environments.

---

## Security Model

- All Terraform state is encrypted at rest (S3 AES-256) and in transit (HTTPS)
- State locking via DynamoDB prevents concurrent apply operations
- GitHub Actions uses **OIDC** — no IAM access keys stored anywhere
- ECS tasks run in private subnets with no inbound internet access
- RDS is in isolated DB subnets — only the ECS security group reaches port 5432
- Secrets (DB password, JWT key) are stored in **AWS Secrets Manager**, injected via the ECS task execution role at runtime
- KMS keys rotate automatically (90-day rotation enabled)

---

## Outputs & Connecting Services

After `terraform apply`, key outputs are available:

```bash
terraform output

# alb_dns_name       = "myproject-staging-alb-123456.us-east-1.elb.amazonaws.com"
# ecs_cluster_name   = "myproject-staging-cluster"
# rds_endpoint       = "myproject-staging.xyz.us-east-1.rds.amazonaws.com"
# ecr_repository_url = "123456789.dkr.ecr.us-east-1.amazonaws.com/backend"
```

Use these values to configure DNS (Route 53) and GitHub Action secrets.
