include .env
export $(shell sed 's/=.*//' .env)

ECR_URL=$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(AWS_REPO_NAME)
TF_DIR=terraform
IMAGE_NAME=memmoney-bot

.PHONY: all build run run-local run-python run-python-local push terraform-init terraform-apply deploy clean migrate migrate-local

all: build run

# Build Docker image
build:
	docker build --platform linux/amd64 -t $(IMAGE_NAME) .

# Run Docker container locally
run: build
	docker run --rm -it \
		--env-file .env \
		--network host \
		$(IMAGE_NAME)

# Run with local development environment variables
run-local: build
	docker run --rm -it \
		-e POSTGRES_HOST=$(POSTGRES_HOST_LOCAL) \
		-e POSTGRES_PORT=$(POSTGRES_PORT_LOCAL) \
		-e POSTGRES_DB=$(POSTGRES_DB_LOCAL) \
		-e POSTGRES_USER=$(POSTGRES_USER_LOCAL) \
		-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD_LOCAL) \
		-e TELEGRAM_BOT_TOKEN=$(TELEGRAM_BOT_TOKEN_DEV) \
		-e AWS_ACCOUNT_ID=$(AWS_ACCOUNT_ID) \
		-e AWS_REGION=$(AWS_REGION) \
		-e AWS_REPO_NAME=$(AWS_REPO_NAME) \
		--network host \
		$(IMAGE_NAME)

# Run in background
run-bg: build
	docker run -d \
		--env-file .env \
		--network host \
		--name memmoney-bot-container \
		$(IMAGE_NAME)

# Run local development in background
run-local-bg: build
	docker run -d \
		-e POSTGRES_HOST=$(POSTGRES_HOST_LOCAL) \
		-e POSTGRES_PORT=$(POSTGRES_PORT_LOCAL) \
		-e POSTGRES_DB=$(POSTGRES_DB_LOCAL) \
		-e POSTGRES_USER=$(POSTGRES_USER_LOCAL) \
		-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD_LOCAL) \
		-e TELEGRAM_BOT_TOKEN=$(TELEGRAM_BOT_TOKEN_DEV) \
		-e AWS_ACCOUNT_ID=$(AWS_ACCOUNT_ID) \
		-e AWS_REGION=$(AWS_REGION) \
		-e AWS_REPO_NAME=$(AWS_REPO_NAME) \
		--network host \
		--name memmoney-bot-local-container \
		$(IMAGE_NAME)

# Stop background container
stop:
	docker stop memmoney-bot-container || true
	docker rm memmoney-bot-container || true

# Stop local development container
stop-local:
	docker stop memmoney-bot-local-container || true
	docker rm memmoney-bot-local-container || true

# Clean up containers and images
clean:
	docker stop memmoney-bot-container || true
	docker rm memmoney-bot-container || true
	docker stop memmoney-bot-local-container || true
	docker rm memmoney-bot-local-container || true
	docker rmi $(IMAGE_NAME) || true

# AWS deployment commands
push: build
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_URL)
	docker tag $(IMAGE_NAME):latest $(ECR_URL):latest
	docker push $(ECR_URL):latest

terraform-init:
	cd $(TF_DIR) && terraform init

terraform-apply:
	cd $(TF_DIR) && terraform apply -auto-approve \
		-var "telegram_token=$(TELEGRAM_BOT_TOKEN)" \
		-var "db_password=$(POSTGRES_PASSWORD)" \
		-var "aws_region=$(AWS_REGION)" \
		-var "account_id=$(AWS_ACCOUNT_ID)" \
		-var "repo_name=$(AWS_REPO_NAME)" \
		-var "db_name=$(POSTGRES_DB)" \
		-var "db_username=$(POSTGRES_USER)" \
		-var "db_port=$(POSTGRES_PORT)" \
		-var "db_instance_class=db.t3.micro" \
		-var "db_allocated_storage=20"

# Get database details from Terraform
get-db-info:
	@echo "📊 Getting database connection details..."
	@cd $(TF_DIR) && terraform output -json > ../db-info.json 2>/dev/null || echo "{}" > ../db-info.json

# Apply database migrations
migrate:
	@echo "🔄 Applying database migrations..."
	@cd $(TF_DIR) && terraform output -raw db_endpoint > /dev/null 2>&1 || { echo "❌ Error: Database not created yet. Run 'make terraform-apply' first."; exit 1; }
	@DB_ENDPOINT=$$(cd $(TF_DIR) && terraform output -raw db_endpoint) && \
	DB_NAME=$$(cd $(TF_DIR) && terraform output -raw db_name) && \
	DB_USERNAME=$$(cd $(TF_DIR) && terraform output -raw db_username) && \
	DB_PASSWORD=$$(cd $(TF_DIR) && terraform output -raw db_password) && \
	echo "🔗 Connecting to: $$DB_ENDPOINT/$$DB_NAME" && \
	flyway -url="jdbc:postgresql://$$DB_ENDPOINT/$$DB_NAME" \
		-user="$$DB_USERNAME" \
		-password="$$DB_PASSWORD" \
		-locations="filesystem:migrations" \
		migrate

migrate-local:
	@echo "🔄 Applying database migrations to localhost..."
	@echo "🔗 Connecting to localhost: $(POSTGRES_HOST_LOCAL):$(POSTGRES_PORT_LOCAL)/$(POSTGRES_DB_LOCAL)" && \
	flyway -url="jdbc:postgresql://$(POSTGRES_HOST_LOCAL):$(POSTGRES_PORT_LOCAL)/$(POSTGRES_DB_LOCAL)" \
		-user="$(POSTGRES_USER_LOCAL)" \
		-password="$(POSTGRES_PASSWORD_LOCAL)" \
		-locations="filesystem:migrations" \
		migrate

deploy: push terraform-init terraform-apply migrate

# Setup and run local development environment
dev-setup: migrate-local run-local

# Setup and run local development in background
dev-setup-bg: migrate-local run-local-bg

# Run Python app directly (without Docker) with production env
run-python:
	@echo "🐍 Starting Python app directly..."
	cd app && python3 bot.py

# Run Python app directly (without Docker) with local env
run-python-local:
	@echo "🐍 Starting Python app directly with local environment..."
	@cd app && \
	POSTGRES_HOST=$(POSTGRES_HOST_LOCAL) \
	POSTGRES_PORT=$(POSTGRES_PORT_LOCAL) \
	POSTGRES_DB=$(POSTGRES_DB_LOCAL) \
	POSTGRES_USER=$(POSTGRES_USER_LOCAL) \
	POSTGRES_PASSWORD=$(POSTGRES_PASSWORD_LOCAL) \
	TELEGRAM_BOT_TOKEN=$(TELEGRAM_BOT_TOKEN_DEV) \
	python3 bot.py

dev-python: migrate-local run-python-local

# Show ECS service info
ecs-info:
	@echo "📊 ECS Service Information:"
	@echo "Cluster: $$(cd $(TF_DIR) && terraform output -raw ecs_cluster_name)"
	@echo "Service: $$(cd $(TF_DIR) && terraform output -raw ecs_service_name)"

# Update ECS service (after pushing new image)
update-ecs: push
	@echo "🔄 Updating ECS service..."
	@aws ecs update-service \
		--cluster $$(cd $(TF_DIR) && terraform output -raw ecs_cluster_name) \
		--service $$(cd $(TF_DIR) && terraform output -raw ecs_service_name) \
		--force-new-deployment
