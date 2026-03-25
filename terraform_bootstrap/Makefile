SHELL := /bin/bash

TERRAFORM ?= terraform
BOOTSTRAP_DIR := bootstrap
AWS_LOCAL_ENV_FILE ?= .aws.local.env
BOOTSTRAP_TFVARS_REL ?= env/bootstrap.tfvars
TFVARS_FILE := $(BOOTSTRAP_DIR)/$(BOOTSTRAP_TFVARS_REL)
TF_DATA_DIR := .terraform

.PHONY: bootstrap bootstrap-init bootstrap-plan bootstrap-apply bootstrap-destroy bootstrap-import-existing

bootstrap: bootstrap-apply

define require_aws_env_file
	@[ -f "$(AWS_LOCAL_ENV_FILE)" ] || { \
		echo "Error: missing AWS env file: $(AWS_LOCAL_ENV_FILE)"; \
		echo "Create it with AWS credentials and region variables."; \
		exit 1; \
	}
endef

define require_bootstrap_tfvars
	@[ -f "$(TFVARS_FILE)" ] || { \
		echo "Error: tfvars file not found: $(TFVARS_FILE)"; \
		exit 1; \
	}
endef

define load_aws_env
set -a; \
source "$(AWS_LOCAL_ENV_FILE)"; \
set +a;
endef

define check_aws_identity
AWS_PAGER="" aws sts get-caller-identity >/dev/null || { \
	echo "Error: AWS authentication failed using $(AWS_LOCAL_ENV_FILE)."; \
	exit 1; \
};
endef

bootstrap-init:
	@$(call require_bootstrap_tfvars)
	@$(call require_aws_env_file)
	@echo "Initializing bootstrap"
	@$(load_aws_env) $(check_aws_identity) cd "$(BOOTSTRAP_DIR)" && TF_DATA_DIR="$(TF_DATA_DIR)" $(TERRAFORM) init

bootstrap-plan:
	@$(call require_bootstrap_tfvars)
	@$(call require_aws_env_file)
	@echo "Planning bootstrap"
	@$(load_aws_env) $(check_aws_identity) cd "$(BOOTSTRAP_DIR)" && TF_DATA_DIR="$(TF_DATA_DIR)" $(TERRAFORM) init -input=false -upgrade && TF_DATA_DIR="$(TF_DATA_DIR)" $(TERRAFORM) plan -var-file="$(BOOTSTRAP_TFVARS_REL)"


bootstrap-apply:
	@$(call require_bootstrap_tfvars)
	@$(call require_aws_env_file)
	@echo "Applying bootstrap"
	@$(load_aws_env) $(check_aws_identity) cd "$(BOOTSTRAP_DIR)" && TF_DATA_DIR="$(TF_DATA_DIR)" $(TERRAFORM) apply -var-file="$(BOOTSTRAP_TFVARS_REL)" -auto-approve

bootstrap-destroy:
	@$(call require_bootstrap_tfvars)
	@$(call require_aws_env_file)
	@echo "Destroying bootstrap"
	@$(load_aws_env) $(check_aws_identity) cd "$(BOOTSTRAP_DIR)" && TF_DATA_DIR="$(TF_DATA_DIR)" $(TERRAFORM) init -input=false -upgrade && TF_DATA_DIR="$(TF_DATA_DIR)" $(TERRAFORM) destroy -var-file="$(BOOTSTRAP_TFVARS_REL)" -auto-approve
