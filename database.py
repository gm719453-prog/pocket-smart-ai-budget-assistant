import os
import sqlite3
import logging
from contextlib import contextmanager
from config import Config

logger = logging.getLogger("pocketsmart.database")
logging.basicConfig(level=logging.INFO)

# Determine primary engine
_USE_SQLITE = False
_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "pocketsmart_local.db")

def test_mysql_connection():
    """Test MySQL connection using config credentials."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            connection_timeout=3
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"MySQL connection attempt failed ({e}). Fallback to local SQLite will be available if needed.")
        return False

def init_db():
    """Initializes tables in MySQL or SQLite fallback."""
    global _USE_SQLITE
    
    if test_mysql_connection():
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            cursor = conn.cursor()
            
            # Read schema.sql
            schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            # Split and execute statements
            statements = schema_sql.split(";")
            for stmt in statements:
                stmt_clean = stmt.strip()
                if stmt_clean and not stmt_clean.lower().startswith("create database") and not stmt_clean.lower().startswith("use "):
                    try:
                        cursor.execute(stmt_clean)
                    except Exception as err:
                        logger.error(f"Error executing schema statement: {err}")
            conn.commit()
            cursor.close()
            conn.close()
            _USE_SQLITE = False
            logger.info("Successfully connected to MySQL and verified schema.")
            return
        except Exception as e:
            logger.warning(f"Failed to initialize MySQL schema: {e}. Switching to SQLite fallback.")
            _USE_SQLITE = True
    else:
        _USE_SQLITE = True

    # SQLite fallback initialization
    logger.info(f"Using SQLite database at {_SQLITE_PATH}")
    conn = sqlite3.connect(_SQLITE_PATH)
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NULL,
        google_id TEXT NULL UNIQUE,
        profile_image TEXT DEFAULT '/static/images/default-avatar.svg',
        monthly_income REAL DEFAULT 0.0,
        currency TEXT DEFAULT '₹',
        theme TEXT DEFAULT 'dark',
        notifications_enabled INTEGER DEFAULT 1,
        ai_insights_enabled INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        expense_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        budget_amount REAL NOT NULL,
        month TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, category, month),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS savings_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        goal_name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        saved_amount REAL DEFAULT 0.0,
        target_date TEXT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS ai_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recommendation_text TEXT NOT NULL,
        source_type TEXT DEFAULT 'gemini',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

def get_connection():
    """Returns a database connection based on active engine."""
    global _USE_SQLITE
    if not _USE_SQLITE:
        try:
            import mysql.connector
            return mysql.connector.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                autocommit=True
            )
        except Exception as e:
            logger.warning(f"MySQL runtime connection failed: {e}. Falling back to SQLite.")
            _USE_SQLITE = True

    conn = sqlite3.connect(_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    """Context manager for safe connection and cursor handling."""
    conn = get_connection()
    is_sqlite = isinstance(conn, sqlite3.Connection)
    cursor = conn.cursor() if is_sqlite else conn.cursor(dictionary=True)
    try:
        yield cursor
        if is_sqlite:
            conn.commit()
    except Exception:
        if is_sqlite:
            conn.rollback()
        raise
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def query_db(query, args=(), one=False):
    """Executes a SELECT query with parameters and returns dictionary rows."""
    global _USE_SQLITE
    with get_db() as cur:
        # Normalize %s placeholders to ? if using SQLite
        if _USE_SQLITE:
            query = query.replace("%s", "?")
            cur.execute(query, args)
            rv = cur.fetchall()
            # Convert sqlite3.Row to regular dict
            rv = [dict(row) for row in rv]
        else:
            cur.execute(query, args)
            rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), return_last_id=False):
    """Executes an INSERT, UPDATE, or DELETE query safely."""
    global _USE_SQLITE
    conn = get_connection()
    is_sqlite = isinstance(conn, sqlite3.Connection)
    cur = conn.cursor() if is_sqlite else conn.cursor()
    last_id = None
    try:
        if is_sqlite:
            sqlite_query = query.replace("%s", "?")
            cur.execute(sqlite_query, args)
            conn.commit()
            last_id = cur.lastrowid
        else:
            cur.execute(query, args)
            conn.commit()
            last_id = cur.lastrowid
        return last_id if return_last_id else cur.rowcount
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def seed_demo_data(user_id):
    """Populates clean demo financial data for college project presentation."""
    from datetime import date
    today = date.today()
    current_month = today.strftime("%Y-%m")
    
    # 1. Update Monthly Income to ₹25,000
    execute_db("UPDATE users SET monthly_income = %s WHERE id = %s", (25000.0, user_id))
    
    # 2. Add sample Budgets
    budgets = [
        ("Food", 5000.0, current_month),
        ("Travel", 3000.0, current_month),
        ("Shopping", 3000.0, current_month),
        ("Education", 2000.0, current_month),
        ("Bills", 2500.0, current_month),
        ("Entertainment", 1500.0, current_month)
    ]
    for cat, amt, mon in budgets:
        # Check if exists
        existing = query_db("SELECT id FROM budgets WHERE user_id = %s AND category = %s AND month = %s", (user_id, cat, mon), one=True)
        if existing:
            execute_db("UPDATE budgets SET budget_amount = %s WHERE id = %s", (amt, existing['id']))
        else:
            execute_db("INSERT INTO budgets (user_id, category, budget_amount, month) VALUES (%s, %s, %s, %s)",
                       (user_id, cat, amt, mon))
            
    # 3. Add sample Expenses for current month
    day_str = today.strftime("%Y-%m-%d")
    sample_expenses = [
        (4500.0, "Food", "Groceries & College Canteen", day_str),
        (2500.0, "Travel", "Monthly Metro Pass & Fuel", day_str),
        (3000.0, "Shopping", "Clothing & Tech Accessories", day_str),
        (2000.0, "Education", "Semester Books & Online Course", day_str),
        (2000.0, "Bills", "Electricity & Mobile Recharge", day_str)
    ]
    
    # Avoid duplicating if already present
    exp_count = query_db("SELECT COUNT(*) as cnt FROM expenses WHERE user_id = %s", (user_id,), one=True)
    if exp_count and exp_count['cnt'] == 0:
        for amt, cat, desc, d in sample_expenses:
            execute_db(
                "INSERT INTO expenses (user_id, amount, category, description, expense_date) VALUES (%s, %s, %s, %s, %s)",
                (user_id, amt, cat, desc, d)
            )
            
    # 4. Add sample Savings Goal
    goal = query_db("SELECT id FROM savings_goals WHERE user_id = %s AND goal_name = %s", (user_id, "New Laptop"), one=True)
    if not goal:
        execute_db(
            "INSERT INTO savings_goals (user_id, goal_name, target_amount, saved_amount) VALUES (%s, %s, %s, %s)",
            (user_id, "New Laptop", 50000.0, 20000.0)
        )
