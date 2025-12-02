include .env
export $(shell sed 's/=.*//' .env)

IMAGE_NAME=memmoney-bot
FLY_APP_NAME ?= memmoney-bot

.PHONY: help run-local dev-setup migrate-local migrate-supabase deploy-fly deploy status logs logs-tail ssh restart set-secrets build run

# ========================================
# Local Development
# ========================================

# Run bot locally with local database
run-local:
	@echo "🐍 Starting bot with local database..."
	@cd app && \
	POSTGRES_HOST=$(POSTGRES_HOST_LOCAL) \
	POSTGRES_PORT=$(POSTGRES_PORT_LOCAL) \
	POSTGRES_DB=$(POSTGRES_DB_LOCAL) \
	POSTGRES_USER=$(POSTGRES_USER_LOCAL) \
	POSTGRES_PASSWORD=$(POSTGRES_PASSWORD_LOCAL) \
	TELEGRAM_BOT_TOKEN=$(TELEGRAM_BOT_TOKEN_DEV) \
	python3 bot.py

# Setup local development environment
dev-setup: migrate-local run-local

# ========================================
# Docker (for local testing)
# ========================================

# Build Docker image
build:
	@echo "🐳 Building Docker image..."
	docker build --platform linux/amd64 -t $(IMAGE_NAME) .

# Run Docker container locally
run: build
	@echo "🐳 Running Docker container locally..."
	docker run --rm -it --env-file .env --network host $(IMAGE_NAME)

# ========================================
# Database Migrations
# ========================================

# Apply migrations to local database
migrate-local:
	@echo "🔄 Applying migrations to local database..."
	@echo "🔗 Connecting to: $(POSTGRES_HOST_LOCAL):$(POSTGRES_PORT_LOCAL)/$(POSTGRES_DB_LOCAL)"
	flyway -url="jdbc:postgresql://$(POSTGRES_HOST_LOCAL):$(POSTGRES_PORT_LOCAL)/$(POSTGRES_DB_LOCAL)" \
		-user="$(POSTGRES_USER_LOCAL)" \
		-password="$(POSTGRES_PASSWORD_LOCAL)" \
		-locations="filesystem:migrations" \
		migrate

# Apply migrations to Supabase (use port 5432 for direct connection)
migrate-supabase:
	@echo "🔄 Applying migrations to Supabase..."
	@echo "🔗 Connecting to: $(SUPABASE_HOST):5432/$(SUPABASE_DB)"
	flyway -url="jdbc:postgresql://$(SUPABASE_HOST):5432/$(SUPABASE_DB)" \
		-user="$(SUPABASE_USER)" \
		-password="$(SUPABASE_PASSWORD)" \
		-locations="filesystem:migrations" \
		migrate

# ========================================
# Fly.io Deployment
# ========================================

# Deploy to Fly.io
deploy-fly:
	@echo "🚀 Deploying to Fly.io..."
	flyctl deploy --app $(FLY_APP_NAME)

# Full deployment (migrate + deploy)
deploy: migrate-supabase deploy-fly
	@echo "✅ Deployment complete!"

# ========================================
# Fly.io Management
# ========================================

# Check app status
status:
	@echo "📊 Fly.io App Status:"
	flyctl status --app $(FLY_APP_NAME)

# View recent logs
logs:
	@echo "📋 Recent Logs:"
	flyctl logs --app $(FLY_APP_NAME)

# Tail logs (follow)
logs-tail:
	@echo "📋 Tailing logs (Ctrl+C to stop)..."
	flyctl logs --app $(FLY_APP_NAME) -f

# SSH into production VM
ssh:
	@echo "🔌 SSH into Fly.io VM..."
	flyctl ssh console --app $(FLY_APP_NAME)

# Restart app
restart:
	@echo "🔄 Restarting app..."
	flyctl apps restart $(FLY_APP_NAME)

# Set Fly.io secrets
set-secrets:
	@echo "🔐 Setting Fly.io secrets..."
	@echo "Note: This uses SUPABASE_* and TELEGRAM_BOT_TOKEN_PROD from .env"
	flyctl secrets set \
		POSTGRES_HOST=$(SUPABASE_HOST) \
		POSTGRES_PORT=$(SUPABASE_PORT) \
		POSTGRES_DB=$(SUPABASE_DB) \
		POSTGRES_USER=$(SUPABASE_USER) \
		POSTGRES_PASSWORD=$(SUPABASE_PASSWORD) \
		TELEGRAM_BOT_TOKEN=$(TELEGRAM_BOT_TOKEN_PROD) \
		--app $(FLY_APP_NAME)

# List current secrets
list-secrets:
	@echo "🔐 Current Fly.io secrets:"
	flyctl secrets list --app $(FLY_APP_NAME)

# Scale app (change VM count)
scale:
	@echo "📏 Current scale:"
	flyctl scale show --app $(FLY_APP_NAME)

# ========================================
# Utilities
# ========================================

# Backup Supabase database
backup:
	@echo "💾 Creating Supabase backup..."
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	PGPASSWORD=$(SUPABASE_PASSWORD) pg_dump \
		-h $(SUPABASE_HOST) -p 5432 \
		-U $(SUPABASE_USER) -d $(SUPABASE_DB) \
		-F p -f backups/supabase_backup_$$TIMESTAMP.sql && \
	gzip backups/supabase_backup_$$TIMESTAMP.sql && \
	echo "✅ Backup saved to: backups/supabase_backup_$$TIMESTAMP.sql.gz"

# Help command
help:
	@echo "MemMoney Bot - Makefile Commands"
	@echo "=================================="
	@echo ""
	@echo "Local Development:"
	@echo "  make run-local        - Run bot with local database"
	@echo "  make dev-setup        - Setup local DB + run bot"
	@echo "  make migrate-local    - Apply migrations to local DB"
	@echo ""
	@echo "Docker:"
	@echo "  make build            - Build Docker image"
	@echo "  make run              - Run Docker container locally"
	@echo ""
	@echo "Database:"
	@echo "  make migrate-supabase - Apply migrations to Supabase"
	@echo "  make backup           - Backup Supabase database"
	@echo ""
	@echo "Fly.io Deployment:"
	@echo "  make deploy           - Full deployment (migrate + deploy)"
	@echo "  make deploy-fly       - Deploy to Fly.io only"
	@echo "  make set-secrets      - Set Fly.io secrets from .env"
	@echo "  make list-secrets     - List current secrets"
	@echo ""
	@echo "Fly.io Management:"
	@echo "  make status           - Show app status"
	@echo "  make logs             - View recent logs"
	@echo "  make logs-tail        - Tail logs (follow)"
	@echo "  make ssh              - SSH into VM"
	@echo "  make restart          - Restart app"
	@echo "  make scale            - Show current scale"
	@echo ""
	@echo "Utilities:"
	@echo "  make help             - Show this help message"