import psycopg2
import requests
from datetime import date
from config import Config

class Database:
    """Database connection and operations class"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                dbname=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                host=Config.DB_HOST,
                port=Config.DB_PORT
            )
        except Exception as e:
            print(f"Database connection failed: {e}")
            raise
    
    def get_cursor(self):
        """Get a database cursor"""
        if not self.connection or self.connection.closed:
            self.connect()
        return self.connection.cursor()
    
    def initialize_user_categories(self, user_id: int):
        """Initialize default categories for a new user"""
        with self.get_cursor() as cur:
            for category in Config.DEFAULT_CATEGORIES:
                cur.execute(
                    """
                    INSERT INTO categories (category_name, user_id)
                    SELECT %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM categories WHERE category_name = %s AND user_id = %s
                    )
                    """,
                    (category, user_id, category, user_id)
                )
            self.connection.commit()
    
    def get_user_categories(self, user_id: int):
        """Get all categories for a user"""
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT id, category_name FROM categories WHERE user_id = %s ORDER BY id",
                (user_id,)
            )
            return cur.fetchall()
    
    def get_category_name(self, category_id: int):
        """Get category name by ID"""
        with self.get_cursor() as cur:
            cur.execute("SELECT category_name FROM categories WHERE id = %s", (category_id,))
            row = cur.fetchone()
            return row[0] if row else "Unknown"
    
    def save_transaction(self, user_id: int, amount: str, currency: str, message: str, category_id: int):
        """Save a new transaction"""
        # Get user's default currency
        user_default_currency = self.get_user_currency(user_id)
        
        # Calculate default currency amount
        if currency.upper() == user_default_currency:
            # If transaction currency is the same as user's default currency, use the same amount
            default_currency_amount = amount
        else:
            # Convert to user's default currency using API rates
            conversion_rate = self.get_conversion_rate(currency, user_default_currency)
            default_currency_amount = float(amount) * conversion_rate
        
        with self.get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (user_id, amount, currency, message, category_id, timestamp, default_currency_amount)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                """,
                (user_id, amount, currency, message, category_id, default_currency_amount)
            )
            self.connection.commit()
    
    def get_user_transactions(self, user_id: int):
        """Get all transactions for a user"""
        with self.get_cursor() as cur:
            cur.execute(
                """
                SELECT t.amount, t.currency, t.message, c.category_name, t.timestamp, t.default_currency_amount
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s
                ORDER BY t.transaction_id
                """,
                (user_id,)
            )
            return cur.fetchall()
    
    def get_transactions_summary(self, user_id: int, time_condition: str = ""):
        """Get transaction summary for a user with optional time filter using default currency amounts"""
        with self.get_cursor() as cur:
            cur.execute(
                f"""
                SELECT c.category_name, SUM(t.default_currency_amount) as total_amount, u.currency as default_currency
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE t.user_id = %s {time_condition}
                GROUP BY c.category_name, u.currency
                ORDER BY total_amount DESC
                """,
                (user_id,)
            )
            return cur.fetchall()
    
    def user_exists(self, user_id: int) -> bool:
        """Check if a user exists in the users table"""
        with self.get_cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            return cur.fetchone() is not None
    
    def create_user(self, user_id: int, currency: str):
        """Create a new user with the specified currency"""
        with self.get_cursor() as cur:
            cur.execute(
                "INSERT INTO users (user_id, currency) VALUES (%s, %s)",
                (user_id, currency)
            )
            self.connection.commit()
    
    def get_user_currency(self, user_id: int) -> str:
        """Get the user's default currency"""
        with self.get_cursor() as cur:
            cur.execute("SELECT currency FROM users WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return row[0] if row else "USD"
    
    def get_conversion_rate(self, from_currency: str, to_currency: str, target_date: date = None) -> float:
        """Get conversion rate from database or fetch from API"""
        if target_date is None:
            target_date = date.today()
        
        # Check if USD rates for this date exist in database
        usd_rates = self.get_cached_usd_rates(target_date)
        if usd_rates:
            # Calculate conversion rate from cached USD rates
            return self.calculate_rate_from_usd_rates(from_currency, to_currency, usd_rates)
        
        # USD rates not found, fetch from API and cache
        return self.fetch_and_cache_usd_rates(target_date, from_currency, to_currency)
    
    def get_cached_usd_rates(self, target_date: date) -> dict:
        """Get cached USD rates for a specific date"""
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT to_currency, rate FROM conversion_rates WHERE date = %s AND from_currency = 'USD'",
                (target_date,)
            )
            rows = cur.fetchall()
            if rows:
                return {row[0].lower(): float(row[1]) for row in rows}
            return {}
    
    def calculate_rate_from_usd_rates(self, from_currency: str, to_currency: str, usd_rates: dict) -> float:
        """Calculate conversion rate from cached USD rates"""
        if from_currency.upper() == 'USD':
            # Direct conversion from USD to target currency
            return usd_rates.get(to_currency.lower(), 1.0)
        elif to_currency.upper() == 'USD':
            # Direct conversion from source currency to USD
            return 1.0 / usd_rates.get(from_currency.lower(), 1.0)
        else:
            # Cross-currency conversion: from_currency -> USD -> to_currency
            from_to_usd_rate = 1.0 / usd_rates.get(from_currency.lower(), 1.0)
            usd_to_target_rate = usd_rates.get(to_currency.lower(), 1.0)
            return from_to_usd_rate * usd_to_target_rate
    
    def fetch_and_cache_usd_rates(self, target_date: date, from_currency: str, to_currency: str) -> float:
        """Fetch USD rates from API and cache them, then calculate the needed conversion rate"""
        try:
            # Fetch USD rates from API
            response = requests.get("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json")
            response.raise_for_status()
            
            api_data = response.json()
            usd_rates = api_data.get('usd', {})
            
            # Cache all USD rates in database
            with self.get_cursor() as cur:
                for currency, rate in usd_rates.items():
                    # Skip currencies with codes longer than 3 characters
                    if len(currency) > 3:
                        print(f"Skipping currency {currency} - code too long")
                        continue
                    
                    cur.execute(
                        """
                        INSERT INTO conversion_rates (date, from_currency, to_currency, rate)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (date, from_currency, to_currency) DO UPDATE SET rate = EXCLUDED.rate
                        """,
                        (target_date, 'USD', currency.upper(), rate)
                    )
                self.connection.commit()
            
            print(f"Cached USD rates for {target_date}: {len(usd_rates)} currencies")
            
            # Calculate and return the needed conversion rate
            return self.calculate_rate_from_usd_rates(from_currency, to_currency, usd_rates)
            
        except Exception as e:
            print(f"Error fetching USD rates: {e}")
            # Fallback to 1:1 conversion if API fails
            return 1.0
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close() 