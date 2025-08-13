import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database import Database
from chart_generator import ChartGenerator
from config import Config

class BotHandlers:
    """Main bot handlers class"""
    
    def __init__(self):
        self.db = Database()
        self.chart_generator = ChartGenerator()
        self.pending_transactions = {}  # Temporary storage for pending transactions
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user_id = update.effective_user.id
        
        # Check if user exists
        if not self.db.user_exists(user_id):
            # Show currency selection
            await self.show_currency_selection(update, context)
            return
        
        # User exists, show welcome message
        await self.show_welcome_message(update, context)
    
    async def show_currency_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show currency selection buttons"""
        currencies = ["GEL", "USD", "RUB", "EUR", "BYN", "KZT", "UAH"]
        
        keyboard = []
        for i in range(0, len(currencies), 2):
            row = []
            row.append(InlineKeyboardButton(currencies[i], callback_data=f"currency_{currencies[i]}"))
            if i + 1 < len(currencies):
                row.append(InlineKeyboardButton(currencies[i + 1], callback_data=f"currency_{currencies[i + 1]}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 Welcome to your personal spending tracker!\n\n"
            "💰 **What is your default currency?**\n"
            "Please select your preferred currency:",
            reply_markup=reply_markup
        )
    
    async def show_welcome_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show welcome message for existing users"""
        user_id = update.effective_user.id
        
        # Initialize user categories
        self.db.initialize_user_categories(user_id)
        
        # Show persistent keyboard menu
        keyboard = [
            [KeyboardButton("🤌 Summarize"), KeyboardButton("🧐 Help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        await update.message.reply_text(
            Config.WELCOME_TEXT,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        await update.message.reply_text(Config.HELP_TEXT)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /menu command"""
        keyboard = [
            [KeyboardButton("🤌 Summarize"), KeyboardButton("🧐 Help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        await update.message.reply_text(
            "🎛️ **Main Menu**\n\nChoose an option:",
            reply_markup=reply_markup
        )
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /list command"""
        user_id = update.effective_user.id
        transactions = self.db.get_user_transactions(user_id)
        
        if not transactions:
            await update.message.reply_text("You have no transactions recorded.")
            return
        
        lines = []
        for amount, currency, message, category_name, timestamp in transactions:
            # Format timestamp as DD-MM-YYYY HH:MM:SS
            formatted_timestamp = timestamp.strftime("%d-%m-%Y %H:%M:%S") if timestamp else "N/A"
            line = f"{amount} {currency} ({formatted_timestamp})"
            if message:
                line += f" — {message}"
            if category_name:
                line += f" [Category: {category_name}]"
            lines.append(line)
        
        await update.message.reply_text("Your transactions:\n" + "\n".join(lines))
    
    async def summarize_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /summarize command"""
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
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages"""
        message = update.message.text.strip()
        
        # Handle keyboard button presses
        if message in ["🤌 Summarize", "🧐 Help"]:
            await self.handle_keyboard_button(update, context, message)
            return
        
        # Handle transaction input - two patterns:
        # 1. Number + currency code (e.g., "100 USD groceries")
        # 2. Just number (e.g., "100 groceries") - uses default currency
        match_with_currency = re.match(r'^(\d+(?:\.\d{1,2})?)\s*([A-Za-z]{3})\b(.*)$', message)
        match_just_number = re.match(r'^(\d+(?:\.\d{1,2})?)\s*(.*)$', message)
        
        if match_with_currency:
            await self.handle_transaction_input(update, context, match_with_currency, has_currency=True)
        elif match_just_number:
            await self.handle_transaction_input(update, context, match_just_number, has_currency=False)
        else:
            await update.message.reply_text("Please send a number (e.g., '100 groceries') or a number with currency (e.g., '100 USD groceries').")
    
    async def handle_transaction_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, match, has_currency: bool) -> None:
        """Handle transaction input and show category selection"""
        user_id = update.effective_user.id
        
        if has_currency:
            # Pattern: number + currency + message
            amount, currency, message_without_amount_currency = match.groups()
            currency = currency.upper()
        else:
            # Pattern: number + message (use default currency)
            amount, message_without_amount_currency = match.groups()
            currency = self.db.get_user_currency(user_id)
        
        # Get categories for the user
        categories = self.db.get_user_categories(user_id)
        if not categories:
            await update.message.reply_text("No categories found. Please use /start to initialize your categories.")
            return
        
        # Store pending transaction
        self.pending_transactions[user_id] = {
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
    
    async def handle_keyboard_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str) -> None:
        """Handle keyboard button presses"""
        if button_text == "🤌 Summarize":
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
            await update.message.reply_text(Config.HELP_TEXT)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries"""
        query = update.callback_query
        data = query.data
        
        print(f"Callback received: {data}")  # Debug print
        
        if data.startswith("summarize_"):
            await self.handle_summarize_callback(update, context)
        elif data.startswith("cat_"):
            await self.handle_category_callback(update, context)
        elif data.startswith("currency_"):
            await self.handle_currency_callback(update, context)
        else:
            print(f"Unknown callback data: {data}")
            await query.answer("Unknown callback")
    
    async def handle_category_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle category selection callback"""
        query = update.callback_query
        data = query.data
        
        # Only process category callbacks
        if not data.startswith("cat_"):
            return
        
        await query.answer()
        user_id = query.from_user.id
        
        print(f"Processing category callback: {data}")  # Debug print
        category_id = int(data.split("_", 1)[1])
        transaction = self.pending_transactions.pop(user_id, None)
        
        if not transaction:
            await query.edit_message_text("No pending transaction found. Please enter your spend again.")
            return
        
        # Get category name and save transaction
        category_name = self.db.get_category_name(category_id)
        self.db.save_transaction(
            user_id, 
            transaction['amount'], 
            transaction['currency'], 
            transaction['message'], 
            category_id
        )
        
        await query.edit_message_text(
            f"All is good. Transaction {transaction['amount']} {transaction['currency']} is written under category: {category_name}."
        )
    
    async def handle_currency_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle currency selection callback"""
        query = update.callback_query
        data = query.data
        
        await query.answer()
        user_id = query.from_user.id
        
        # Extract currency from callback data
        currency = data.replace("currency_", "")
        
        # Create user with selected currency
        self.db.create_user(user_id, currency)
        
        # Initialize user categories
        self.db.initialize_user_categories(user_id)
        
        # First, edit the original message to confirm currency selection
        await query.edit_message_text(
            f"✅ Perfect! Your default currency is set to **{currency}**."
        )
        
        # Then send a new message with the persistent keyboard
        keyboard = [
            [KeyboardButton("🤌 Summarize"), KeyboardButton("🧐 Help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=Config.WELCOME_TEXT.format(currency=currency),
            reply_markup=reply_markup
        )
    
    async def handle_summarize_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle summarize callback"""
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
        
        # Get transaction data
        category_totals = self.db.get_transactions_summary(user_id, sql_condition)
        
        if not category_totals:
            await query.edit_message_text(f"You have no transactions for {period_title.lower()}.")
            return
        
        # Prepare data for the chart
        categories = []
        amounts = []
        currency = category_totals[0][2] if category_totals else "USD"
        
        for category_name, total_amount, curr in category_totals:
            if category_name:  # Only include categorized transactions
                categories.append(category_name)
                amounts.append(float(total_amount))
        
        if not categories:
            await query.edit_message_text(f"You have no categorized transactions for {period_title.lower()}.")
            return
        
        # Create and send chart
        chart_buffer = self.chart_generator.create_spending_chart(categories, amounts, currency, period_title)
        
        # Delete the time selection message
        try:
            await query.delete_message()
        except:
            pass  # Ignore if message can't be deleted
        
        # Send the chart
        await context.bot.send_photo(
            chat_id=query.from_user.id,
            photo=chart_buffer,
            caption=f"📊 Spending Summary - {period_title}\n💰 Total: {sum(amounts):.2f} {currency}"
        )
        
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
    
    def cleanup(self):
        """Cleanup resources"""
        self.db.close() 