Project Composition
Enterprise Multi-Infrastructure DevOps Project

1. Project Composition

Application Stack (shared across all infra projects)
	•	Backend: Python (FastAPI)
	•	Frontend: Angular
	•	Database: PostgreSQL (AWS RDS)
	•	Containerization: Docker
	•	Environments: Dev, Staging, Prod

Deployment Strategies / Infra Repos

Repo / Infra	Compute	Deployment	CI/CD	IaC
platform-infra-fargate	ECS Fargate	Terraform	GitHub Actions	Terraform modules
platform-infra-ec2	EC2 + ASG	Ansible (provision) + Terraform	GitHub Actions	Terraform + Ansible
platform-infra-eks	EKS	GitOps (ArgoCD + Helm)	GitHub Actions → ArgoCD	Terraform modules + Helm charts


⸻

1. Architecture Overview

2.1 Shared Components
	•	Networking: VPC per infra, multi-AZ subnets, NAT gateway, private/public segregation
	•	IAM: Least privilege, separate roles per CI/CD, per service, per environment
	•	Logging & Monitoring: CloudWatch for all infra; Prometheus + Grafana for EKS
	•	Security: Encrypted RDS/ECR, security groups per service, CloudTrail & GuardDuty

2.2 Fargate Infra

          +-------------------------+
          |        ALB              |
          +-----------+-------------+
                      |
           +----------+----------+
           | ECS Cluster (Fargate)|
           +----+----------+-----+
           |    |          |     |
       Backend Frontend  Workers  # optional
          |     |          |
         ECR   ECR        ECR
          |
        CloudWatch logs
          |
         RDS (private)

2.3 EC2 + Ansible Infra

         +----------------------+
         |        ALB           |
         +-----------+----------+
                     |
           +---------+----------+
           | EC2 ASG (Backend) |
           | EC2 ASG (Frontend)|
           +---------+----------+
                     |
                   Ansible Playbooks
                     |
                  CloudWatch Logs
                     |
                    RDS (private)

2.4 EKS + ArgoCD + Helm Infra

Root App (ArgoCD)
 ├── Non-Prod Cluster (EKS)
 │    ├── Namespace: dev
 │    │     ├── backend
 │    │     └── frontend
 │    └── Namespace: staging
 │          ├── backend
 │          └── frontend
 └── Prod Cluster (EKS)
      └── Namespace: prod
            ├── backend
            └── frontend
                |
                Helm charts
                |
                RDS (private)

	•	App-of-Apps pattern for dev/staging/prod
	•	Manual approval for prod
	•	Prometheus + Grafana + CloudWatch for monitoring

⸻

3. Terraform Modules (per repo)

Common modules
	•	vpc/ → VPC, subnets, NAT, route tables, security groups
	•	iam/ → Roles for CI/CD, service accounts, ECS/EKS nodes
	•	ecr/ → Docker repos for backend/frontend
	•	rds/ → PostgreSQL with encryption, backups, multi-AZ
	•	security/ → SGs, NACLs, private endpoints

Infra-specific modules
	•	Fargate: ecs-cluster/, ecs-service/, alb/
	•	EC2: ec2/, alb/
	•	EKS: eks/, helm-charts/ (values per env)

⸻

4. CI/CD Strategy

Infra	Pipeline Flow
Fargate	Build Docker → Push ECR → Terraform apply ECS → CloudWatch logs
EC2	Build Docker → Push ECR → Ansible deploy → CloudWatch logs
EKS	Build Docker → Push ECR → Update Helm values → ArgoCD auto-sync (dev/staging) / manual sync (prod) → Prometheus + Grafana metrics

	•	Speculative Terraform plan before merge
	•	Manual approval for prod deployments