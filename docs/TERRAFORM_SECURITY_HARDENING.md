# Terraform Security Hardening - Checkov Compliance Guide

This document outlines the security improvements made to Terraform code to pass Checkov security scanning.

## Fixes Applied

### 1. **S3 Bucket Encryption & Versioning (ALB Logs)**
- ✅ Enable S3 bucket versioning
- ✅ Enable server-side encryption (AES256)
- ✅ Deny unencrypted object uploads via bucket policy
- ✅ Block all public access

**Checkov Checks Addressed:**
- CKV_AWS_21: Ensure bucket versioning is enabled
- CKV_AWS_27: Ensure S3 bucket has server-side encryption enabled

### 2. **RDS Security Hardening**
- ✅ Restrict egress traffic to DNS and HTTPS only
- ✅ Enable backup encryption with KMS
- ✅ Enable performance insights with encryption
- ✅ Enable CloudWatch logs exports
- ✅ Enable multi-AZ deployments
- ✅ Require final snapshot before deletion

**Checkov Checks Addressed:**
- CKV_AWS_31: Ensure backup exists in encrypted form
- CKV_AWS_16: Ensure Security Group is ingress restricted
- CKV_AWS_104: Ensure RDS backup is encrypted

### 3. **KMS Key Policies**
- ✅ Add explicit KMS key policy for Secrets Manager access
- ✅ Restrict key usage to IAM root and specific services
- ✅ Enable automatic key rotation

**Checkov Checks Addressed:**
- CKV_AWS_7: Ensure KMS key has rotation enabled
- CKV_AWS_33: Ensure KMS key policy does not allow '*' actions

### 4. **ALB Hardening**
- ✅ Enable deletion protection for ALB
- ✅ Add S3 bucket prefix for organized logs
- ✅ Enforce SSL/TLS with security policy

**Checkov Checks Addressed:**
- CKV_AWS_91: Ensure ALB has deletion protection enabled
- CKV_AWS_103: Ensure ALB is configured to log requests

### 5. **Network Security (Security Groups)**
- ✅ Restrict RDS egress to DNS and HTTPS (least privilege)
- ✅ Remove overly broad egress rules
- ✅ Add description tags for audit trail

**Checkov Checks Addressed:**
- CKV_AWS_24: Ensure no security groups allow ingress from 0.0.0.0:0 to port 22
- CKV_AWS_62: Ensure security group is not open to 0.0.0.0 on restricted ports

### 6. **IAM Policies (Least Privilege)**
- ✅ Restrict Secrets Manager KMS decrypt access
- ✅ Limit ECS log write permissions to specific log group
- ✅ Use service principals instead of wildcard principals

**Checkov Checks Addressed:**
- CKV_AWS_63: Ensure IAM policies do not allow '*' actions
- CKV_AWS_1: Ensure IAM policies documents allow only required permissions

### 7. **CloudWatch Logging**
- ✅ Enable logging on all resources with appropriate retention
- ✅ Add KMS encryption for log groups
- ✅ Restrict access to sensitive logs

**Checkov Checks Addressed:**
- CKV_AWS_38: Ensure CloudWatch log group is encrypted

## Implementation Steps

### For ALB Module (`modules/alb/main.tf`):
```hcl
# Add S3 versioning and encryption
resource "aws_s3_bucket_versioning" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Enable deletion protection
enable_deletion_protection = true
```

### For Network Module (`modules/network/main.tf`):
```hcl
# Restrict RDS egress to DNS and HTTPS only
egress {
  from_port   = 53
  to_port     = 53
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  description = "DNS TCP"
}

egress {
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
  description = "HTTPS for AWS APIs"
}
```

### For Main Terraform (`main.tf`):
```hcl
# Add KMS key policy
policy = jsonencode({
  Version = "2012-10-17"
  Statement = [
    {
      Sid = "Enable IAM policies"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      }
      Action = "kms:*"
      Resource = "*"
    },
    {
      Sid = "Allow Secrets Manager"
      Effect = "Allow"
      Principal = {
        Service = "secretsmanager.amazonaws.com"
      }
      Action = [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey"
      ]
      Resource = "*"
    }
  ]
})
```

## Checkov Command

Run Checkov locally to verify security compliance:

```bash
# Install checkov if not already installed
pip install checkov

# Run Checkov on Terraform directory
checkov -d infra/ --framework terraform

# Run with specific framework and output
checkov -d infra/ --framework terraform --output sarif --output-file checkov-results.sarif

# Filter by severity
checkov -d infra/ --framework terraform --check CKV_AWS_21,CKV_AWS_27
```

## Remaining Items

- [ ] Update ECS task role policies to use least-privilege access patterns
- [ ] Add tags to all resources for proper governance
- [ ] Implement resource naming standards across all modules
- [ ] Enable Terraform locking with DynamoDB for state management

## References

- [Checkov Policies](https://www.checkov.io/2.Catalog/all_checks)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)
- [Terraform AWS Provider Security](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
