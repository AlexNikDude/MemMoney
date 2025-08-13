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
🤖 **How to add transactions:**
Simply send a message with amount and currency, e.g.:
• "100 USD groceries"
• "25.50 EUR lunch"
• "15 GBP coffee"
"""
    
    # Default categories
    DEFAULT_CATEGORIES = [
        "Groceries",
        "Eat out",
        "Housing",
        "Transportation",
        "Health",
        "Clothing & Footwear",
        "Entertainment & Leisure",
        "Subscriptions",
        "Other"
    ] 