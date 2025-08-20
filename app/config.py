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
• "100" (we'll use your default currency {currency})
• "25.50 USD" (if you set currency the amount will be recorded in specified currency)
• "15 USD coffee" (you can add additional messages)
"""
    
    # Welcome text with currency (for new users)
    WELCOME_TEXT = """👋 Welcome to your personal spending tracker!

💡 **How to add transactions:**
Simply send a message with amount, e.g.:
• "100" (we'll use your default currency {currency})
• "25.50 USD" (if you set currency the amount will be recorded in specified currency)
• "15 USD coffee" (you can add additional messages)

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