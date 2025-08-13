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

#### Production
```bash
# Run with Docker (production environment)
make run

# Run Docker in background
make run-bg

# Run Python directly (production environment)
make run-python
```

### Available Make Commands

```bash
# Local Development (No Docker)
make run-local          # Run app with local environment variables
make dev-setup          # Setup DB + run app locally

# Production (Docker)
make run               # Run with Docker (production env)
make run-bg            # Run Docker in background
make run-python        # Run Python directly (production env)

# Database
make migrate-local     # Run migrations on local database
make migrate           # Run migrations on production database

# Deployment
make deploy            # Deploy to AWS
```

### Environment Files

- **`.env`** - Contains both local and production environment variables
- **Local variables**: `POSTGRES_HOST_LOCAL`, `POSTGRES_DB_LOCAL`, `TELEGRAM_BOT_TOKEN_DEV`, etc.
- **Production variables**: `POSTGRES_HOST`, `POSTGRES_DB`, `TELEGRAM_BOT_TOKEN`, etc.

## 🔧 Benefits of Refactoring

### 1. **Maintainability**
- **Single Responsibility**: Each module has one clear purpose
- **Easy to Modify**: Change chart styling without touching database code
- **Clear Dependencies**: Each module imports only what it needs

### 2. **Testability**
- **Isolated Components**: Test database operations separately from bot logic
- **Mock Support**: Easy to mock dependencies for unit tests
- **Clear Interfaces**: Well-defined method signatures

### 3. **Scalability**
- **Modular Design**: Add new features without affecting existing code
- **Reusable Components**: Chart generator can be used for other features
- **Clean Architecture**: Easy to extend and modify

### 4. **Code Quality**
- **No Duplication**: Shared constants and logic
- **Type Hints**: Better code documentation
- **Error Handling**: Centralized error management
- **Logging**: Proper debug output

## 🎯 Key Improvements

### Before (Single File)
- ❌ 400+ lines in one file
- ❌ Mixed concerns (DB, UI, logic)
- ❌ Duplicated code
- ❌ Hard to test
- ❌ Difficult to maintain

### After (Modular)
- ✅ 5 focused modules
- ✅ Clear separation of concerns
- ✅ No code duplication
- ✅ Easy to test
- ✅ Simple to maintain



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
- **Connection Pooling**: Database connections are managed properly
- **Cleanup**: Proper resource cleanup on shutdown

The MemMoney bot provides a clean, maintainable codebase with all the features you need for personal spending tracking! 🎉 