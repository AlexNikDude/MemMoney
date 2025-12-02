# MemMoney Bot

## 🏗️ Project Structure

A clean, maintainable MemMoney bot for tracking personal spending with beautiful charts and easy-to-use interface:

```
TelegramBot/
├── config.py              # Configuration and constants
├── database.py            # Database operations
├── chart_generator.py     # Chart creation logic
├── handlers.py            # Bot command and callback handlers
├── bot.py                 # Main bot file
├── requirements.txt       # Python dependencies
├── migrations/            # Database migrations
├── flyway.conf           # Database migration config
└── README.md             # This file
```

## 📁 Module Overview

### `config.py`
- **Purpose**: Centralized configuration management
- **Contains**: 
  - Database connection settings
  - Bot token
  - Help text constants
  - Default categories
- **Benefits**: Easy to modify settings, no hardcoded values

### `database.py`
- **Purpose**: Database operations abstraction
- **Contains**: 
  - Database connection management
  - User category operations
  - Transaction CRUD operations
  - Summary queries
- **Benefits**: Clean database interface, connection pooling, error handling

### `chart_generator.py`
- **Purpose**: Chart creation and styling
- **Contains**: 
  - Pie chart generation
  - Styling and theming
  - Image buffer creation
- **Benefits**: Reusable chart logic, easy to modify styling

### `handlers.py`
- **Purpose**: Bot command and callback handling
- **Contains**: 
  - All command handlers (`/start`, `/help`, etc.)
  - Message processing
  - Callback query handling
  - Transaction flow logic
- **Benefits**: Organized handlers, clear separation of concerns

### `bot_refactored.py`
- **Purpose**: Main bot entry point
- **Contains**: 
  - Application setup
  - Handler registration
  - Bot startup logic
- **Benefits**: Clean main file, easy to understand flow

## 🚀 How to Run

### Environment Setup

The project supports separate environment configurations for local development and production:

#### Local Development
```bash
# Activate virtual environment
source .venv/bin/activate

# Run app with local environment variables
make run-local

# Or setup database and run app locally
make dev-setup
```

#### Production (Fly.io + Supabase)
```bash
# Deploy to Fly.io (includes database migrations)
make deploy

# Or deploy without migrations
make deploy-fly

# View app status
make status

# View logs
make logs-tail
```

### Available Make Commands

```bash
# Local Development
make run-local          # Run bot with local database
make dev-setup          # Setup local DB + run bot
make migrate-local      # Apply migrations to local DB

# Docker (for testing)
make build              # Build Docker image
make run                # Run Docker container locally

# Database
make migrate-supabase   # Apply migrations to Supabase
make backup             # Backup Supabase database

# Fly.io Deployment
make deploy             # Full deployment (migrate + deploy)
make deploy-fly         # Deploy to Fly.io only
make set-secrets        # Set Fly.io secrets from .env
make list-secrets       # List current secrets

# Fly.io Management
make status             # Show app status
make logs               # View recent logs
make logs-tail          # Tail logs (follow)
make ssh                # SSH into VM
make restart            # Restart app
make scale              # Show current scale
```

## 🛠️ Development Workflow

### Adding New Features
1. **Database changes** → Modify `database.py`
2. **UI changes** → Modify `handlers.py`
3. **Chart changes** → Modify `chart_generator.py`
4. **Configuration changes** → Modify `config.py`

### Adding New Commands
1. Add method to `BotHandlers` class in `handlers.py`
2. Register handler in `bot.py`
3. Update help text in `config.py` if needed

## 📊 Performance Benefits

- **Faster Startup**: Only load what's needed
- **Memory Efficient**: Better resource management
- **Connection Pooling**: Supabase provides built-in connection pooling (port 6543)
- **Cleanup**: Proper resource cleanup on shutdown

## 🌐 Deployment

The MemMoney bot is deployed on:
- **Fly.io** (Amsterdam region) - Free tier, 512MB RAM
- **Supabase** (PostgreSQL) - Free tier, 500MB storage, connection pooling included

The MemMoney bot provides a clean, maintainable codebase with all the features you need for personal spending tracking! 🎉 