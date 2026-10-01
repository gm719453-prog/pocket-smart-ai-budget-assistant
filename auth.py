import re
import logging
from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from authlib.integrations.flask_client import OAuth
from config import Config
from database import query_db, execute_db

logger = logging.getLogger("pocketsmart.auth")

# Token serializer for password reset
serializer = URLSafeTimedSerializer(Config.SECRET_KEY)

# OAuth instance
oauth = OAuth()

def init_oauth(app):
    """Initializes Google OAuth with Flask app."""
    oauth.init_app(app)
    if Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET:
        oauth.register(
            name="google",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"}
        )
        logger.info("Google OAuth 2.0 registered successfully.")
    else:
        logger.info("Google OAuth credentials not provided in .env. OAuth will display configuration guidance.")

def login_required(f):
    """Decorator to protect routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def validate_email_format(email):
    """Simple regex to validate email address format."""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email.strip()) is not None

def register_user(name, email, password, confirm_password):
    """Registers a new user with email and hashed password."""
    name = (name or "").strip()
    email = (email or "").strip().lower()
    
    if not name or not email or not password or not confirm_password:
        return False, "All fields are required."
    
    if not validate_email_format(email):
        return False, "Please enter a valid email address."
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
        
    if password != confirm_password:
        return False, "Passwords do not match."
        
    # Check if email is already registered
    existing_user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
    if existing_user:
        return False, "An account with this email already exists."
        
    pwd_hash = generate_password_hash(password, method="scrypt")
    try:
        user_id = execute_db(
            "INSERT INTO users (name, email, password_hash, monthly_income) VALUES (%s, %s, %s, %s)",
            (name, email, pwd_hash, 0.0),
            return_last_id=True
        )
        return True, user_id
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return False, "An error occurred while creating your account. Please try again."

def authenticate_user(email, password):
    """Validates user credentials and returns user record or None."""
    email = (email or "").strip().lower()
    if not email or not password:
        return None, "Email and password are required."
        
    user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
    if not user:
        # Prevent timing attack / user enumeration
        return None, "Email or password is incorrect."
        
    if not user.get("password_hash"):
        # Account registered via Google OAuth without password
        return None, "This account was registered using Google. Please log in with Google."
        
    if check_password_hash(user["password_hash"], password):
        return user, None
        
    return None, "Email or password is incorrect."

def get_current_user():
    """Returns the currently logged-in user dictionary from database."""
    if "user_id" not in session:
        return None
    return query_db("SELECT * FROM users WHERE id = %s", (session["user_id"],), one=True)

def generate_reset_token(email):
    """Generates a secure timed token for password reset."""
    return serializer.dumps(email, salt="password-reset-salt")

def verify_reset_token(token, max_age_seconds=3600):
    """Verifies a reset token and returns email if valid."""
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=max_age_seconds)
        return email
    except (SignatureExpired, BadTimeSignature):
        return None
