import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import re

from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = int(os.getenv('POSTGRES_PORT', 5432))
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

import psycopg2
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    default_categories = [
        "Groceries",
        "Eat out",
        "Housing",
        "Transportation",
        "Health",
        "Clothing & Footwear",
        "Entertainment & Leisure",
        "Gifts",
        "Other"
    ]
    with conn.cursor() as cur:
        for cat in default_categories:
            cur.execute(
                """
                INSERT INTO categories (category_name, user_id)
                SELECT %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM categories WHERE category_name = %s AND user_id = %s
                )
                """,
                (cat, user_id, cat, user_id)
            )
        conn.commit()
    await update.message.reply_text('Hello. \n Enter the amount of money you spent..')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Send /start to get a welcome message. Send /help to see this message.')

# In-memory storage for transactions
transactions = {}

# Temporary storage for pending transactions
pending_transactions = {}

async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text.strip()
    match = re.match(r'^(\d+(?:\.\d{1,2})?)\s*([A-Za-z]{3})\b(.*)$', message)
    if match:
        amount, currency, message_without_amount_currency = match.groups()
        user_id = update.effective_user.id
        # Fetch categories for the user
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, category_name FROM categories WHERE user_id = %s ORDER BY id",
                (str(user_id),)
            )
            categories = cur.fetchall()
        if not categories:
            await update.message.reply_text("No categories found. Please use /start to initialize your categories.")
            return
        # Store pending transaction
        pending_transactions[user_id] = {
            'amount': amount,
            'currency': currency.upper(),
            'message': message_without_amount_currency.strip()
        }
        # Show categories as buttons
        keyboard = [
            [InlineKeyboardButton(cat_name, callback_data=f"cat_{cat_id}")]
            for cat_id, cat_name in categories
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Please select a category for this transaction:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Please send a number followed by a 3-letter currency code, e.g. '100 USD'.")

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if not data.startswith("cat_"):
        return
    category_id = int(data.split("_", 1)[1])
    transaction = pending_transactions.pop(user_id, None)
    if not transaction:
        await query.edit_message_text("No pending transaction found. Please enter your spend again.")
        return
    # Get category name
    with conn.cursor() as cur:
        cur.execute("SELECT category_name FROM categories WHERE id = %s", (category_id,))
        row = cur.fetchone()
        category_name = row[0] if row else "Unknown"
        # Save transaction to DB
        cur.execute(
            """
            INSERT INTO transactions (user_id, amount, currency, message, category_id, timestamp)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (str(user_id), transaction['amount'], transaction['currency'], transaction['message'], category_id)
        )
        conn.commit()
    await query.edit_message_text(f"All is good. Transaction {transaction['amount']} {transaction['currency']} is written under category: {category_name}.")

async def list_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.amount, t.currency, t.message, c.category_name, t.timestamp
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s
            ORDER BY t.transaction_id
            """,
            (str(user_id),)
        )
        user_transactions = cur.fetchall()
    if not user_transactions:
        await update.message.reply_text("You have no transactions recorded.")
        return
    lines = []
    for amount, currency, message, category_name, timestamp in user_transactions:
        # Format timestamp as DD-MM-YYYY HH:MM:SS
        formatted_timestamp = timestamp.strftime("%d-%m-%Y %H:%M:%S") if timestamp else "N/A"
        line = f"{amount} {currency} ({formatted_timestamp})"
        if message:
            line += f" — {message}"
        if category_name:
            line += f" [Category: {category_name}]"
        lines.append(line)
    await update.message.reply_text("Your transactions:\n" + "\n".join(lines))

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('list', list_transactions))
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    app.add_handler(CallbackQueryHandler(category_selected))
    app.run_polling()
