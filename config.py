import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (local development only)
load_dotenv()

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "pocketsmart_secure_fallback_key_2026")

    # Database settings — environment variables with Railway MYSQL* fallback
    DB_HOST = os.getenv("DB_HOST") or os.getenv("MYSQLHOST") or "localhost"
    DB_PORT = int(os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or 3306)
    DB_USER = os.getenv("DB_USER") or os.getenv("MYSQLUSER") or "root"
    DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD") or ""
    DB_NAME = os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE") or "pocketsmart"

    # Google Gemini AI settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    # Google OAuth 2.0 settings
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set SESSION_COOKIE_SECURE=True in production (requires HTTPS)
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")

    # Server configuration
    # IMPORTANT: DEBUG must be False in production. Set FLASK_DEBUG=True only in local .env
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    PORT = int(os.getenv("PORT", 5000))
