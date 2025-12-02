# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MemMoney Bot is a Telegram bot for personal spending tracking with category-based organization, multi-currency support, and visual spending summaries. The bot is deployed on Fly.io with Supabase PostgreSQL database (both free tier).

## Development Commands

### Local Development
```bash
# Run bot locally with local database
make run-local

# Setup local database and run
make dev-setup

# Run database migrations on local database
make migrate-local
```

### Docker (for local testing)
```bash
# Build Docker image
make build

# Run with Docker locally
make run
```

### Database Management
```bash
# Apply migrations to Supabase (production)
make migrate-supabase

# Apply migrations to local database
make migrate-local

# Backup Supabase database
make backup
```

### Fly.io Deployment
```bash
# Full deployment (migrate + deploy)
make deploy

# Deploy to Fly.io only
make deploy-fly

# Set secrets from .env
make set-secrets

# List current secrets
make list-secrets
```

### Fly.io Management
```bash
# Check app status
make status

# View logs
make logs

# Tail logs (follow)
make logs-tail

# SSH into VM
make ssh

# Restart app
make restart

# Show scale info
make scale
```

## Architecture

### Module Structure

The application follows a modular architecture with clear separation of concerns:

- **`app/bot.py`** - Main entry point. Sets up the Telegram bot application, registers all command handlers, and manages the bot lifecycle. Also configures the bot menu commands visible to users.

- **`app/config.py`** - Centralized configuration. Loads environment variables and defines constants including database settings, bot token, help text, welcome messages, and default spending categories.

- **`app/database.py`** - Database abstraction layer. The `Database` class manages PostgreSQL connections and provides methods for all database operations including user management, transactions, categories, and currency conversion rates.

- **`app/handlers.py`** - Bot interaction logic. The `BotHandlers` class contains all command handlers (`/start`, `/help`, `/list`, `/summarize`, `/menu`), message processing, callback query handling, and transaction flow orchestration.

- **`app/chart_generator.py`** - Visualization logic. The `ChartGenerator` class creates pie charts for spending summaries using matplotlib with custom dark theme styling.

### Database Schema

The application uses PostgreSQL with Flyway migrations (in `migrations/` directory):

- **`users`** - Stores user profiles with their default currency
- **`categories`** - User-specific spending categories
- **`transactions`** - Individual spending records with amount, currency, message, category, timestamp, and converted amount in user's default currency
- **`conversion_rates`** - Cached currency exchange rates from USD to other currencies

### Currency Conversion System

The bot supports multi-currency transactions with automatic conversion:

1. Each user has a default currency set during onboarding
2. Users can record transactions in any currency (e.g., "100 USD" or "50 EUR")
3. All transactions are stored in their original currency
4. Additionally, a `default_currency_amount` is calculated and stored for each transaction
5. Currency conversion rates are fetched from an external API and cached in the database
6. The cache stores USD-to-X rates for all currencies, allowing cross-currency calculations
7. Summary views and charts use the `default_currency_amount` to aggregate spending across currencies

### Transaction Flow

1. User sends a message with amount (e.g., "100" or "100 USD groceries")
2. Bot parses the amount, optional currency code, and optional description
3. If no currency specified, uses user's default currency
4. Bot shows category selection buttons
5. User selects a category via inline keyboard
6. Transaction is saved with original currency and converted amount
7. Conversion rate is fetched from API if not cached, then cached for future use

### Deployment Architecture

- **Fly.io** - Runs the containerized bot (512MB RAM, free tier, Amsterdam region)
- **Supabase PostgreSQL** - Managed database with connection pooling (free tier: 500MB storage)
- **Fly.io Registry** - Stores Docker images
- **fly.toml** - Infrastructure configuration
- **Environment Variables** - `.env` file contains local, deprecated AWS, and Supabase configurations

**Database Connection Strategy:**
- **Port 5432** (direct connection) - Used only for Flyway migrations
- **Port 6543** (pooled connection) - Used by the bot application for better connection management
- Supabase provides built-in connection pooling in transaction mode

## Key Implementation Details

### Environment Configuration

The project uses a single `.env` file with three sets of variables:
- **Local variables**: `POSTGRES_HOST_LOCAL`, `POSTGRES_DB_LOCAL`, `TELEGRAM_BOT_TOKEN_DEV`, etc.
- **AWS variables (deprecated)**: Kept for reference, AWS account is blocked
- **Supabase variables**: `SUPABASE_HOST`, `SUPABASE_PORT`, `SUPABASE_USER`, `SUPABASE_PASSWORD`, `TELEGRAM_BOT_TOKEN_PROD`, etc.

The `Makefile` handles switching between local and production by setting environment variables when running commands. For Fly.io deployment, secrets are set using `flyctl secrets set` which reads from SUPABASE_* variables in `.env`.

### Bot Command Registration

The bot automatically registers its commands in the Telegram menu using the `post_init` callback in `bot.py`. This ensures users see available commands in their Telegram client.

### Persistent Keyboard

After user onboarding, the bot displays a persistent keyboard with quick-access buttons for "Summarize" and "Help" actions, making the interface more user-friendly.

### Callback Query Routing

Callback queries (from inline keyboards) are routed based on prefixes:
- `currency_*` - Currency selection during onboarding
- `cat_*` - Category selection for transactions
- `summarize_*` - Time period selection for spending summaries

### Summary Time Periods

The `/summarize` command offers four time periods:
- This Month (current calendar month)
- Last 7 Days
- Last 30 Days
- All Transactions

Summaries aggregate spending by category using SQL and display results as a pie chart plus text breakdown.

## Code Patterns

### Database Connection Management

The `Database` class maintains a persistent connection and automatically reconnects if closed. Always use `with self.get_cursor() as cur:` pattern to ensure proper cursor cleanup.

### Handler Pattern

All bot handlers are methods of the `BotHandlers` class, which maintains state including the database connection, chart generator, and pending transactions dictionary.

### Cleanup

The `BotHandlers.cleanup()` method ensures database connections are properly closed when the bot stops.

## Testing Changes

When making changes:

1. Test locally first using `make run-local` with local database
2. Verify database migrations work with `make migrate-local`
3. Test Docker build with `make run` (optional)
4. Test Supabase migrations with `make migrate-supabase`
5. Deploy to Fly.io with `make deploy` after successful local testing
6. Monitor logs with `make logs-tail` to verify deployment

## Important Notes

- The bot uses async/await patterns with python-telegram-bot library
- All user IDs are stored as BIGINT in the database (standardized in V10 migration)
- Currency codes must be 3 characters or less (enforced in database.py)
- The chart generator creates 16x12 inch charts with 150 DPI for high-quality visuals
- Flyway is used for database migrations with versioned SQL files
- **Supabase connection**: Always use port 6543 (pooled) for application, port 5432 (direct) only for migrations
- **Fly.io secrets**: Set using `make set-secrets` which reads from `.env` file
- **Backups**: Use `make backup` to create timestamped Supabase backups, or `scripts/backup-supabase.sh` directly