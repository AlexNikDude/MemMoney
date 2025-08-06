import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from handlers import BotHandlers
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    """Main function to run the bot"""
    # Create bot handlers instance
    handlers = BotHandlers()
    
    # Build the application
    app = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler('start', handlers.start_command))
    app.add_handler(CommandHandler('help', handlers.help_command))
    app.add_handler(CommandHandler('list', handlers.list_command))
    app.add_handler(CommandHandler('summarize', handlers.summarize_command))
    app.add_handler(CommandHandler('menu', handlers.menu_command))
    
    # Add message and callback handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    app.add_handler(CallbackQueryHandler(handlers.handle_callback_query))
    
    # Start the bot
    print("🤖 Bot is starting...")
    app.run_polling()
    
    # Cleanup when bot stops
    handlers.cleanup()

if __name__ == '__main__':
    main() 