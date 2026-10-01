import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "pocketsmart_secure_fallback_key_2026")
    
    # Database settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "pocketsmart")
    
    # Google Gemini AI settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    
    # Google OAuth 2.0 settings
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # Server configuration
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
