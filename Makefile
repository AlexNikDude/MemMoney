include .env
export $(shell sed 's/=.*//' .env)

ECR_URL=$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(AWS_REPO_NAME)
TF_DIR=terraform
IMAGE_NAME=memmoney-bot

.PHONY: all build run push terraform-init terraform-apply deploy clean migrate

all: build run

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run Docker container locally
run: build
	docker run --rm -it \
		--env-file .env \
		--network host \
		$(IMAGE_NAME)

# Run in background
run-bg: build
	docker run -d \
		--env-file .env \
		--network host \
		--name memmoney-bot-container \
		$(IMAGE_NAME)

# Stop background container
stop:
	docker stop memmoney-bot-container || true
	docker rm memmoney-bot-container || true

# Clean up containers and images
clean:
	docker stop memmoney-bot-container || true
	docker rm memmoney-bot-container || true
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

deploy: push terraform-init terraform-apply migrate
