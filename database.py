import psycopg2
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
    
    def initialize_user_categories(self, user_id: str):
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
    
    def get_user_categories(self, user_id: str):
        """Get all categories for a user"""
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT id, category_name FROM categories WHERE user_id = %s ORDER BY id",
                (str(user_id),)
            )
            return cur.fetchall()
    
    def get_category_name(self, category_id: int):
        """Get category name by ID"""
        with self.get_cursor() as cur:
            cur.execute("SELECT category_name FROM categories WHERE id = %s", (category_id,))
            row = cur.fetchone()
            return row[0] if row else "Unknown"
    
    def save_transaction(self, user_id: str, amount: str, currency: str, message: str, category_id: int):
        """Save a new transaction"""
        with self.get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (user_id, amount, currency, message, category_id, timestamp)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (str(user_id), amount, currency, message, category_id)
            )
            self.connection.commit()
    
    def get_user_transactions(self, user_id: str):
        """Get all transactions for a user"""
        with self.get_cursor() as cur:
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
            return cur.fetchall()
    
    def get_transactions_summary(self, user_id: str, time_condition: str = ""):
        """Get transaction summary for a user with optional time filter"""
        with self.get_cursor() as cur:
            cur.execute(
                f"""
                SELECT c.category_name, SUM(t.amount) as total_amount, t.currency
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s {time_condition}
                GROUP BY c.category_name, t.currency
                ORDER BY total_amount DESC
                """,
                (str(user_id),)
            )
            return cur.fetchall()
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close() 