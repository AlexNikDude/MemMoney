include .env
export $(shell sed 's/=.*//' .env)

ECR_URL=$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(AWS_REPO_NAME)
TF_DIR=terraform
IMAGE_NAME=memmoney-bot

.PHONY: all build run push terraform-init terraform-apply deploy clean

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

deploy: push terraform-init terraform-apply
