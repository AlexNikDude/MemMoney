import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import re
import matplotlib.pyplot as plt
import io
import os

from dotenv import load_dotenv

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
    
    # Show persistent keyboard menu
    keyboard = [
        [KeyboardButton("🤌 Summarize"), KeyboardButton("🧐 Help")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        '👋 Hello! Welcome to your personal spending tracker.\n\n'
        '💡 **How to add transactions:**\n'
        'Simply send a message with amount and currency, e.g.:\n'
        '• "100 USD groceries"\n'
        '• "25.50 EUR lunch"\n'
        '• "15 GBP coffee"\n\n'
        'Use the buttons below for quick access:',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main menu with buttons"""
    keyboard = [
        [KeyboardButton("🤌 Summarize"), KeyboardButton("🧐 Help")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        "🎛️ **Main Menu**\n\nChoose an option:",
        reply_markup=reply_markup
    )



# Help text constant to avoid duplication
HELP_TEXT = """
🤖 **How to add transactions:**
Simply send a message with amount and currency, e.g.:
• "100 USD groceries"
• "25.50 EUR lunch"
• "15 GBP coffee"
"""

# In-memory storage for transactions
transactions = {}

# Temporary storage for pending transactions
pending_transactions = {}

async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text.strip()
    
    # Handle keyboard button presses
    if message in ["🤌 Summarize", "🧐 Help"]:
        await handle_keyboard_button(update, context, message)
        return
    
    # Handle transaction input
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

async def handle_keyboard_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str) -> None:
    """Handle keyboard button presses"""
    if button_text == "🤌 Summarize":
        # Show time period selection buttons
        keyboard = [
            [InlineKeyboardButton("📅 This Month", callback_data="summarize_this_month")],
            [InlineKeyboardButton("📅 Last 7 Days", callback_data="summarize_7_days")],
            [InlineKeyboardButton("📅 Last 30 Days", callback_data="summarize_30_days")],
            [InlineKeyboardButton("📅 All Transactions", callback_data="summarize_all")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📊 Choose a time period for your spending summary:",
            reply_markup=reply_markup
        )
    
    elif button_text == "🧐 Help":
        await update.message.reply_text(HELP_TEXT)
    


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    
    # Only process category callbacks
    if not data.startswith("cat_"):
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    print(f"Processing category callback: {data}")  # Debug print
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

async def summarize_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Show time period selection buttons
    keyboard = [
        [InlineKeyboardButton("📅 This Month", callback_data="summarize_this_month")],
        [InlineKeyboardButton("📅 Last 7 Days", callback_data="summarize_7_days")],
        [InlineKeyboardButton("📅 Last 30 Days", callback_data="summarize_30_days")],
        [InlineKeyboardButton("📅 All Transactions", callback_data="summarize_all")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📊 Choose a time period for your spending summary:",
        reply_markup=reply_markup
    )

async def handle_summarize_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    
    # Only process summarize callbacks
    if not data.startswith("summarize_"):
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    print(f"Processing summarize callback: {data}")  # Debug print
    
    period = data.replace("summarize_", "")
    
    # Build the SQL query based on the selected period
    if period == "this_month":
        sql_condition = "AND EXTRACT(MONTH FROM t.timestamp) = EXTRACT(MONTH FROM CURRENT_DATE) AND EXTRACT(YEAR FROM t.timestamp) = EXTRACT(YEAR FROM CURRENT_DATE)"
        period_title = "This Month"
    elif period == "7_days":
        sql_condition = "AND t.timestamp >= CURRENT_DATE - INTERVAL '7 days'"
        period_title = "Last 7 Days"
    elif period == "30_days":
        sql_condition = "AND t.timestamp >= CURRENT_DATE - INTERVAL '30 days'"
        period_title = "Last 30 Days"
    elif period == "all":
        sql_condition = ""
        period_title = "All Time"
    else:
        await query.edit_message_text("Invalid time period selected.")
        return
    
    # Get transaction data grouped by category for the selected period
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT c.category_name, SUM(t.amount) as total_amount, t.currency
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s {sql_condition}
            GROUP BY c.category_name, t.currency
            ORDER BY total_amount DESC
            """,
            (str(user_id),)
        )
        category_totals = cur.fetchall()
    
    if not category_totals:
        await query.edit_message_text(f"You have no transactions for {period_title.lower()}.")
        return
    
    # Prepare data for the chart
    categories = []
    amounts = []
    currency = category_totals[0][2] if category_totals else "USD"  # Use first currency found
    
    for category_name, total_amount, curr in category_totals:
        if category_name:  # Only include categorized transactions
            categories.append(category_name)
            amounts.append(float(total_amount))
    
    if not categories:
        await query.edit_message_text(f"You have no categorized transactions for {period_title.lower()}.")
        return
    
    # Set dark theme
    plt.style.use('dark_background')
    
    # Create beautiful colors with gradients
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
              '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
    
    # Create the chart with enhanced styling - bigger size
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Custom autopct function to show both percentage and amount
    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return f'{pct:.1f}%\n({val:.0f})'
        return my_autopct
    
    # Create pie chart with enhanced styling
    wedges, texts, autotexts = ax.pie(
        amounts, 
        labels=categories, 
        autopct=make_autopct(amounts),
        startangle=90,
        colors=colors[:len(amounts)],
        explode=[0.05] * len(amounts),  # Slight separation between slices
        textprops={'fontsize': 12, 'color': 'white', 'weight': 'bold'},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )
    
    # Enhance autopct text styling
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(11)
        autotext.set_weight('bold')
    
    # Add title with enhanced styling - centered at top
    plt.suptitle(
        f'Spending by Category - ({currency})', 
        fontsize=24, 
        fontweight='bold', 
        color='white',
        y=0.85
    )
    
    # Add total amount as subtitle at bottom
    plt.figtext(
        0.5, 0.06, 
        f'Total Spent: {sum(amounts):.2f} {currency}', 
        ha='center', 
        fontsize=16, 
        fontweight='bold',
        color='#FFD700'  # Gold color for total
    )
    
    # Set background to black
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    
    # Center the pie chart with better margins and more free space
    ax.set_position([0.1, 0.15, 0.8, 0.65])  # [left, bottom, width, height]
    
    # Save the chart to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(
        buf, 
        format='png', 
        bbox_inches='tight', 
        dpi=150,
        facecolor='black',
        edgecolor='none',
        transparent=False
    )
    buf.seek(0)
    plt.close()
    
    # Delete the time selection message
    try:
        await query.delete_message()
    except:
        pass  # Ignore if message can't be deleted
    
    # Send the chart
    await context.bot.send_photo(
        chat_id=query.from_user.id,
        photo=buf    )
    
    # Also send a text summary
    summary_lines = [f"📊 **Spending Summary - {period_title}:**"]
    for i, (category, amount) in enumerate(zip(categories, amounts), 1):
        percentage = (amount / sum(amounts)) * 100
        summary_lines.append(f"{i}. {category}: {amount:.2f} {currency} ({percentage:.1f}%)")
    
    summary_lines.append(f"\n💰 **Total Spent**: {sum(amounts):.2f} {currency}")
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="\n".join(summary_lines)
    )
    
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unified callback handler that routes to appropriate functions"""
    query = update.callback_query
    data = query.data
    
    print(f"Callback received: {data}")  # Debug print
    
    if data.startswith("summarize_"):
        await handle_summarize_callback(update, context)
    elif data.startswith("cat_"):
        await category_selected(update, context)
    else:
        print(f"Unknown callback data: {data}")
        await query.answer("Unknown callback")



if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('list', list_transactions))
    app.add_handler(CommandHandler('summarize', summarize_transactions))
    app.add_handler(CommandHandler('menu', menu_command))
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.run_polling()
