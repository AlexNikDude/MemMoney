import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the Telegram bot"""
    
    # Database configuration
    DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    DB_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
    DB_USER = os.getenv('POSTGRES_USER', 'postgres')
    DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    
    # Bot configuration
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Help text constant
    HELP_TEXT = """
🤖 How to add transactions: 🤖

Simply send a message with amount and currency, for example:
"100" - as simple as possible, we'll use your default currency {currency}
"25 USD" - you can specify currency if needed (use three-letter currency code)
"15 USD coffee" - you can add any text to describe your spends
"""
    
    # Default categories
    DEFAULT_CATEGORIES = [
        "Groceries",
        "Eat out & Food delivery",
        "Housing",
        "Transportation",
        "Health & Beauty",
        "Clothing & Footwear",
        "Entertainment & Leisure",
        "Subscriptions",
        "Other"
    ] 