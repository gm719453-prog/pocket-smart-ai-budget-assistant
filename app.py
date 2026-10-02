import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from config import Config
from database import init_db, query_db, execute_db, seed_demo_data
from auth import (
    init_oauth, oauth, login_required, register_user, authenticate_user,
    get_current_user, generate_reset_token, verify_reset_token
)
from ai_service import get_ai_recommendations, build_spending_summary_data
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# Initialize OAuth and Database
init_oauth(app)
with app.app_context():
    init_db()

# Context processor to inject user, current year, and currency into all templates
@app.context_processor
def inject_global_data():
    current_user = get_current_user() if "user_id" in session else None
    currency = current_user.get("currency", "₹") if current_user else "₹"
    theme = current_user.get("theme", "dark") if current_user else "dark"
    return {
        "current_user": current_user,
        "currency": currency,
        "active_theme": theme,
        "now_year": datetime.now().year,
        "current_date": date.today().strftime("%Y-%m-%d"),
        "current_month": date.today().strftime("%Y-%m")
    }

# ============================================================
# 1. LANDING & AUTHENTICATION ROUTES
# ============================================================

@app.route("/")
def index():
    """Landing Page with rich modern aesthetics and animations."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """User Login route supporting email/password and Google OAuth entry."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        user, error_msg = authenticate_user(email, password)
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session.permanent = True
            flash(f"Welcome back, {user['name']}! 👋", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard"))
        else:
            flash(error_msg or "Email or password is incorrect.", "danger")
            return render_template("login.html", email=email), 401

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """New User Registration route with input validation and password hashing."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        success, result = register_user(name, email, password, confirm_password)
        if success:
            user_id = result
            # Log the new user in automatically
            session.clear()
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_email"] = email
            session.permanent = True
            flash("Account created successfully! Welcome to PocketSmart AI 🚀", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(result, "danger")
            return render_template("signup.html", name=name, email=email), 400

    return render_template("signup.html")

@app.route("/auth/google")
def google_login():
    """Initiates Google OAuth 2.0 flow."""
    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        flash("Google OAuth credentials are not configured in .env. Please sign up or log in using Email & Password.", "warning")
        return redirect(url_for("login"))
    redirect_uri = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/auth/google/callback")
def google_callback():
    """Handles Google OAuth 2.0 authorization callback."""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo") or oauth.google.userinfo()
        
        if not user_info or not user_info.get("email"):
            flash("Failed to retrieve user information from Google. Please try again.", "danger")
            return redirect(url_for("login"))
            
        google_id = user_info.get("sub")
        email = user_info.get("email").lower().strip()
        name = user_info.get("name", email.split("@")[0])
        picture = user_info.get("picture", "/static/images/default-avatar.svg")
        
        # Check if user already exists
        user = query_db("SELECT * FROM users WHERE email = %s OR google_id = %s", (email, google_id), one=True)
        if user:
            # Update google_id and picture if not set
            execute_db("UPDATE users SET google_id = %s, profile_image = %s WHERE id = %s",
                       (google_id, picture, user["id"]))
            user_id = user["id"]
            user_name = user["name"]
        else:
            # Create new user for Google login
            user_id = execute_db(
                "INSERT INTO users (name, email, google_id, profile_image, monthly_income) VALUES (%s, %s, %s, %s, %s)",
                (name, email, google_id, picture, 0.0),
                return_last_id=True
            )
            user_name = name
            
        session.clear()
        session["user_id"] = user_id
        session["user_name"] = user_name
        session["user_email"] = email
        session.permanent = True
        flash(f"Logged in successfully with Google! Welcome, {user_name} 👋", "success")
        return redirect(url_for("dashboard"))
        
    except Exception as e:
        flash("Google authentication could not be completed. Please try again or use email login.", "danger")
        return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Handles password reset request with secure token generation."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if email:
            user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
            if user:
                token = generate_reset_token(email)
                # Store reset token record in DB
                expires_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                execute_db("INSERT INTO password_resets (user_id, token, expires_at) VALUES (%s, %s, %s)",
                           (user["id"], token, expires_at))
                
                # In college demo / development, provide reset link directly
                reset_link = url_for("reset_password", token=token, _external=True)
                flash(f"If an account exists for this email, password reset instructions will be sent.", "info")
                return render_template("forgot_password.html", reset_link_demo=reset_link, email=email)
            else:
                # Do not reveal whether user exists
                flash("If an account exists for this email, password reset instructions will be sent.", "info")
                return render_template("forgot_password.html", email=email)
        else:
            flash("Please enter your email address.", "danger")
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Allows resetting password using a valid cryptographic token."""
    email = verify_reset_token(token)
    if not email:
        flash("Password reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for("forgot_password"))
        
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            pwd_hash = generate_password_hash(password, method="scrypt")
            execute_db("UPDATE users SET password_hash = %s WHERE email = %s", (pwd_hash, email))
            flash("Password reset successfully! Please log in with your new password.", "success")
            return redirect(url_for("login"))
            
    return render_template("reset_password.html", token=token)

@app.route("/logout")
def logout():
    """Destroys current session and redirects to login."""
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("login"))

# ============================================================
# 2. DASHBOARD & STATS ROUTES
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():
    """Main Dashboard with financial metric cards, alerts, and charts."""
    user_id = session["user_id"]
    summary = build_spending_summary_data(user_id)
    
    # Financial metrics
    income = summary["income"]
    total_budget = summary["total_budget"]
    total_expenses = summary["total_expenses"]
    remaining_budget = max(total_budget - total_expenses, 0.0) if total_budget > 0 else max(income - total_expenses, 0.0)
    
    # Total savings amount accumulated across goals
    savings_query = query_db(
        "SELECT SUM(saved_amount) as total_saved, SUM(target_amount) as total_target "
        "FROM savings_goals WHERE user_id = %s", (user_id,), one=True
    )
    total_savings = float(savings_query["total_saved"] or 0.0) if savings_query else 0.0
    
    # Budget usage percentage
    budget_usage_pct = round((total_expenses / total_budget * 100), 1) if total_budget > 0 else 0.0
    
    # Budget alerts
    budget_alerts = []
    for cat, spent in summary["category_expenses"].items():
        if cat in summary["category_budgets"]:
            limit = summary["category_budgets"][cat]
            if limit > 0:
                pct = (spent / limit) * 100
                if pct >= 100:
                    budget_alerts.append({
                        "category": cat,
                        "type": "danger",
                        "message": f"Your {cat} budget has been exceeded! Spent: {summary['currency']}{spent:,.2f} of {summary['currency']}{limit:,.2f}"
                    })
                elif pct >= 85:
                    budget_alerts.append({
                        "category": cat,
                        "type": "warning",
                        "message": f"You're getting close to your {cat} budget limit ({pct:.1f}% used)."
                    })

    # Recent 5 transactions
    recent_expenses = query_db(
        "SELECT * FROM expenses WHERE user_id = %s ORDER BY expense_date DESC, id DESC LIMIT 5",
        (user_id,)
    )

    # Active savings goals (up to 3)
    savings_goals = query_db(
        "SELECT * FROM savings_goals WHERE user_id = %s ORDER BY id DESC LIMIT 3",
        (user_id,)
    )

    return render_template(
        "dashboard.html",
        income=income,
        total_budget=total_budget,
        total_expenses=total_expenses,
        remaining_budget=remaining_budget,
        total_savings=total_savings,
        budget_usage_pct=budget_usage_pct,
        budget_alerts=budget_alerts,
        recent_expenses=recent_expenses,
        savings_goals=savings_goals,
        summary=summary
    )

@app.route("/api/chart-data")
@login_required
def chart_data():
    """Provides categorized data for Chart.js visualizations."""
    user_id = session["user_id"]
    summary = build_spending_summary_data(user_id)
    
    # 1. Category Breakdown for Doughnut Chart
    cat_labels = list(summary["category_expenses"].keys())
    cat_values = list(summary["category_expenses"].values())
    
    # 2. Monthly Trend (last 6 months)
    # We query monthly aggregations for user
    monthly_trend_query = query_db(
        "SELECT SUBSTRING(expense_date, 1, 7) as mon, SUM(amount) as total "
        "FROM expenses WHERE user_id = %s "
        "GROUP BY mon ORDER BY mon ASC LIMIT 6",
        (user_id,)
    )
    month_labels = [row["mon"] for row in monthly_trend_query] or [summary["month"]]
    month_values = [float(row["total"]) for row in monthly_trend_query] or [summary["total_expenses"]]
    
    # 3. Budget vs Spent Comparison
    budget_cats = list(summary["category_budgets"].keys())
    budget_vals = [summary["category_budgets"][c] for c in budget_cats]
    spent_vals = [summary["category_expenses"].get(c, 0.0) for c in budget_cats]
    
    # 4. Savings Goals
    savings_goals = query_db("SELECT goal_name, target_amount, saved_amount FROM savings_goals WHERE user_id = %s", (user_id,))
    s_names = [g["goal_name"] for g in savings_goals]
    s_saved = [float(g["saved_amount"] or 0) for g in savings_goals]
    s_target = [float(g["target_amount"] or 0) for g in savings_goals]

    return jsonify({
        "success": True,
        "currency": summary["currency"],
        "category_chart": {
            "labels": cat_labels,
            "data": cat_values
        },
        "monthly_trend": {
            "labels": month_labels,
            "data": month_values
        },
        "budget_vs_spent": {
            "labels": budget_cats,
            "budgets": budget_vals,
            "spent": spent_vals
        },
        "savings_chart": {
            "labels": s_names,
            "saved": s_saved,
            "target": s_target
        }
    })

# ============================================================
# 3. INCOME MANAGEMENT
# ============================================================

@app.route("/income", methods=["GET"])
@login_required
def income():
    """Displays monthly income overview and update form."""
    user = query_db("SELECT monthly_income, currency FROM users WHERE id = %s", (session["user_id"],), one=True)
    income_val = float(user["monthly_income"] or 0.0) if user else 0.0
    return render_template("income.html", income=income_val)

@app.route("/income/update", methods=["POST"])
@login_required
def update_income():
    """Updates user monthly income."""
    try:
        income_val = float(request.form.get("income", 0))
        if income_val < 0:
            flash("Monthly income cannot be negative.", "danger")
            return redirect(url_for("income"))
            
        execute_db("UPDATE users SET monthly_income = %s WHERE id = %s", (income_val, session["user_id"]))
        flash(f"Monthly income updated successfully!", "success")
    except ValueError:
        flash("Please enter a valid numeric income amount.", "danger")
        
    return redirect(url_for("dashboard"))

# ============================================================
# 4. EXPENSES MANAGEMENT (CRUD)
# ============================================================

EXPENSE_CATEGORIES = [
    "Food", "Travel", "Shopping", "Education", 
    "Bills", "Entertainment", "Health", "Other"
]

@app.route("/expenses")
@login_required
def expenses():
    """Displays list of user expenses with search, category & date filters."""
    user_id = session["user_id"]
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    sort_by = request.args.get("sort_by", "date_desc")

    query = "SELECT * FROM expenses WHERE user_id = %s"
    params = [user_id]

    if search:
        query += " AND (description LIKE %s OR category LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    if category and category != "All":
        query += " AND category = %s"
        params.append(category)

    if start_date:
        query += " AND expense_date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND expense_date <= %s"
        params.append(end_date)

    if sort_by == "date_asc":
        query += " ORDER BY expense_date ASC, id ASC"
    elif sort_by == "amount_desc":
        query += " ORDER BY amount DESC, expense_date DESC"
    elif sort_by == "amount_asc":
        query += " ORDER BY amount ASC, expense_date DESC"
    else:
        query += " ORDER BY expense_date DESC, id DESC"

    user_expenses = query_db(query, tuple(params))
    total_spent = sum(float(e["amount"]) for e in user_expenses)

    return render_template(
        "expenses.html",
        expenses=user_expenses,
        categories=EXPENSE_CATEGORIES,
        total_spent=total_spent,
        search=search,
        selected_category=category,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by
    )

@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    """Add new expense transaction."""
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            category = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()
            expense_date = request.form.get("expense_date", date.today().strftime("%Y-%m-%d"))

            if amount <= 0:
                flash("Please enter an amount greater than 0.", "danger")
                return render_template("add_expense.html", categories=EXPENSE_CATEGORIES)

            if not category or category not in EXPENSE_CATEGORIES:
                flash("Please select a valid expense category.", "danger")
                return render_template("add_expense.html", categories=EXPENSE_CATEGORIES)

            if not description:
                flash("Please provide a short description.", "danger")
                return render_template("add_expense.html", categories=EXPENSE_CATEGORIES)

            execute_db(
                "INSERT INTO expenses (user_id, amount, category, description, expense_date) "
                "VALUES (%s, %s, %s, %s, %s)",
                (session["user_id"], amount, category, description, expense_date)
            )
            flash("Expense added successfully!", "success")
            return redirect(url_for("expenses"))
        except ValueError:
            flash("Please enter a valid numeric amount.", "danger")
            return render_template("add_expense.html", categories=EXPENSE_CATEGORIES)

    return render_template("add_expense.html", categories=EXPENSE_CATEGORIES)

@app.route("/expenses/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    """Edit an existing expense record."""
    user_id = session["user_id"]
    expense = query_db("SELECT * FROM expenses WHERE id = %s AND user_id = %s", (expense_id, user_id), one=True)
    if not expense:
        flash("Expense not found or unauthorized access.", "danger")
        return redirect(url_for("expenses"))

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            category = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()
            expense_date = request.form.get("expense_date", expense["expense_date"])

            if amount <= 0:
                flash("Amount must be greater than 0.", "danger")
                return render_template("edit_expense.html", expense=expense, categories=EXPENSE_CATEGORIES)

            execute_db(
                "UPDATE expenses SET amount = %s, category = %s, description = %s, expense_date = %s "
                "WHERE id = %s AND user_id = %s",
                (amount, category, description, expense_date, expense_id, user_id)
            )
            flash("Expense updated successfully!", "success")
            return redirect(url_for("expenses"))
        except ValueError:
            flash("Please enter a valid numeric amount.", "danger")

    return render_template("edit_expense.html", expense=expense, categories=EXPENSE_CATEGORIES)

@app.route("/expenses/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    """Delete an expense record."""
    user_id = session["user_id"]
    rows = execute_db("DELETE FROM expenses WHERE id = %s AND user_id = %s", (expense_id, user_id))
    if rows > 0:
        flash("Expense deleted successfully.", "info")
    else:
        flash("Unable to delete expense or record not found.", "danger")
    return redirect(url_for("expenses"))

# ============================================================
# 5. BUDGET MANAGEMENT
# ============================================================

@app.route("/budget")
@login_required
def budget():
    """Displays category budgets, spent amounts, remaining balance, and usage progress."""
    user_id = session["user_id"]
    current_month = date.today().strftime("%Y-%m")
    
    # Fetch budgets for user in current month
    user_budgets = query_db(
        "SELECT * FROM budgets WHERE user_id = %s AND month = %s ORDER BY budget_amount DESC",
        (user_id, current_month)
    )

    # Fetch total spent per category in current month
    month_pattern = f"{current_month}%"
    spent_records = query_db(
        "SELECT category, SUM(amount) as total_spent FROM expenses "
        "WHERE user_id = %s AND expense_date LIKE %s GROUP BY category",
        (user_id, month_pattern)
    )
    spent_map = {row["category"]: float(row["total_spent"]) for row in spent_records}

    budget_items = []
    total_budget_sum = 0.0
    total_spent_sum = 0.0

    for b in user_budgets:
        cat = b["category"]
        b_amt = float(b["budget_amount"])
        spent = spent_map.get(cat, 0.0)
        remaining = max(b_amt - spent, 0.0)
        pct = round((spent / b_amt * 100), 1) if b_amt > 0 else 0.0
        
        status = "normal"
        status_msg = "Within spending limit"
        if pct >= 100:
            status = "exceeded"
            status_msg = f"Your {cat} budget has been exceeded!"
        elif pct >= 85:
            status = "warning"
            status_msg = f"You're getting close to your {cat} budget."

        budget_items.append({
            "id": b["id"],
            "category": cat,
            "budget_amount": b_amt,
            "spent": spent,
            "remaining": remaining,
            "percentage": pct,
            "status": status,
            "status_message": status_msg
        })
        total_budget_sum += b_amt
        total_spent_sum += spent

    remaining_total = max(total_budget_sum - total_spent_sum, 0.0)
    overall_pct = round((total_spent_sum / total_budget_sum * 100), 1) if total_budget_sum > 0 else 0.0

    return render_template(
        "budget.html",
        budget_items=budget_items,
        total_budget=total_budget_sum,
        total_spent=total_spent_sum,
        remaining_total=remaining_total,
        overall_pct=overall_pct,
        categories=EXPENSE_CATEGORIES,
        current_month=current_month
    )

@app.route("/budget/add", methods=["POST"])
@login_required
def add_budget():
    """Creates or updates a monthly budget for a specific category."""
    user_id = session["user_id"]
    category = request.form.get("category", "").strip()
    month = request.form.get("month", date.today().strftime("%Y-%m"))
    
    try:
        amount = float(request.form.get("budget_amount", 0))
        if amount <= 0:
            flash("Budget amount must be greater than 0.", "danger")
            return redirect(url_for("budget"))

        # Check existing budget for user/cat/month
        existing = query_db(
            "SELECT id FROM budgets WHERE user_id = %s AND category = %s AND month = %s",
            (user_id, category, month),
            one=True
        )
        if existing:
            execute_db("UPDATE budgets SET budget_amount = %s WHERE id = %s", (amount, existing["id"]))
            flash(f"Budget for {category} updated to {amount:,.2f}!", "success")
        else:
            execute_db(
                "INSERT INTO budgets (user_id, category, budget_amount, month) VALUES (%s, %s, %s, %s)",
                (user_id, category, amount, month)
            )
            flash(f"Budget for {category} created successfully!", "success")
    except ValueError:
        flash("Please enter a valid numeric budget amount.", "danger")

    return redirect(url_for("budget"))

@app.route("/budget/edit/<int:budget_id>", methods=["POST"])
@login_required
def edit_budget(budget_id):
    """Updates an existing category budget amount."""
    user_id = session["user_id"]
    try:
        amount = float(request.form.get("budget_amount", 0))
        if amount <= 0:
            flash("Budget amount must be greater than 0.", "danger")
        else:
            execute_db("UPDATE budgets SET budget_amount = %s WHERE id = %s AND user_id = %s",
                       (amount, budget_id, user_id))
            flash("Budget updated successfully.", "success")
    except ValueError:
        flash("Invalid numeric amount.", "danger")
    return redirect(url_for("budget"))

@app.route("/budget/delete/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    """Deletes a category budget."""
    user_id = session["user_id"]
    execute_db("DELETE FROM budgets WHERE id = %s AND user_id = %s", (budget_id, user_id))
    flash("Budget deleted successfully.", "info")
    return redirect(url_for("budget"))

# ============================================================
# 6. SAVINGS GOALS
# ============================================================

@app.route("/savings")
@login_required
def savings():
    """Displays active savings goals with target, saved amount, and progress."""
    user_id = session["user_id"]
    goals = query_db("SELECT * FROM savings_goals WHERE user_id = %s ORDER BY id DESC", (user_id,))
    
    enriched_goals = []
    total_target = 0.0
    total_saved = 0.0

    for g in goals:
        target = float(g["target_amount"] or 0)
        saved = float(g["saved_amount"] or 0)
        remaining = max(target - saved, 0.0)
        pct = min(round((saved / target * 100), 1) if target > 0 else 0.0, 100.0)

        enriched_goals.append({
            "id": g["id"],
            "goal_name": g["goal_name"],
            "target_amount": target,
            "saved_amount": saved,
            "remaining": remaining,
            "percentage": pct,
            "target_date": g.get("target_date")
        })
        total_target += target
        total_saved += saved

    overall_savings_pct = round((total_saved / total_target * 100), 1) if total_target > 0 else 0.0

    return render_template(
        "savings.html",
        goals=enriched_goals,
        total_target=total_target,
        total_saved=total_saved,
        overall_pct=overall_savings_pct
    )

@app.route("/savings/add", methods=["POST"])
@login_required
def add_savings_goal():
    """Creates a new savings goal."""
    user_id = session["user_id"]
    name = request.form.get("goal_name", "").strip()
    target_date = request.form.get("target_date", None) or None
    
    try:
        target = float(request.form.get("target_amount", 0))
        saved = float(request.form.get("saved_amount", 0) or 0)
        
        if not name:
            flash("Please enter a goal name.", "danger")
            return redirect(url_for("savings"))
            
        if target <= 0:
            flash("Target amount must be greater than 0.", "danger")
            return redirect(url_for("savings"))
            
        execute_db(
            "INSERT INTO savings_goals (user_id, goal_name, target_amount, saved_amount, target_date) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, name, target, saved, target_date)
        )
        flash(f"Savings goal '{name}' created successfully!", "success")
    except ValueError:
        flash("Please enter valid numeric amounts.", "danger")

    return redirect(url_for("savings"))

@app.route("/savings/update", methods=["POST"])
@login_required
def update_savings_amount():
    """Adds or updates saved amount for a goal."""
    user_id = session["user_id"]
    goal_id = request.form.get("goal_id")
    action = request.form.get("action", "add") # 'add' funds or 'set' amount
    
    try:
        amount = float(request.form.get("amount", 0))
        if amount <= 0 and action == "add":
            flash("Amount to deposit must be greater than 0.", "danger")
            return redirect(url_for("savings"))
            
        goal = query_db("SELECT * FROM savings_goals WHERE id = %s AND user_id = %s", (goal_id, user_id), one=True)
        if not goal:
            flash("Savings goal not found.", "danger")
            return redirect(url_for("savings"))
            
        current_saved = float(goal["saved_amount"] or 0)
        new_amount = (current_saved + amount) if action == "add" else amount
        
        execute_db("UPDATE savings_goals SET saved_amount = %s WHERE id = %s AND user_id = %s",
                   (new_amount, goal_id, user_id))
                   
        flash(f"Updated funds for '{goal['goal_name']}'! Saved balance: {new_amount:,.2f}", "success")
    except ValueError:
        flash("Invalid numeric value.", "danger")

    return redirect(url_for("savings"))

@app.route("/savings/delete/<int:goal_id>", methods=["POST"])
@login_required
def delete_savings_goal(goal_id):
    """Deletes a savings goal."""
    user_id = session["user_id"]
    execute_db("DELETE FROM savings_goals WHERE id = %s AND user_id = %s", (goal_id, user_id))
    flash("Savings goal deleted successfully.", "info")
    return redirect(url_for("savings"))

# ============================================================
# 7. AI INSIGHTS & RECOMMENDATIONS (GEMINI & 429 SHIELD)
# ============================================================

@app.route("/recommendations")
@login_required
def recommendations():
    """Renders the AI Insights view with past recommendation history."""
    user_id = session["user_id"]
    summary = build_spending_summary_data(user_id)
    user = query_db("SELECT ai_insights_enabled FROM users WHERE id = %s", (user_id,), one=True)
    ai_enabled = bool(user.get("ai_insights_enabled", 1)) if user else True
    
    # Retrieve past AI recommendations stored in DB
    past_recs = query_db(
        "SELECT * FROM ai_recommendations WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
        (user_id,)
    )

    return render_template(
        "recommendations.html",
        summary=summary,
        past_recommendations=past_recs,
        ai_enabled=ai_enabled
    )

@app.route("/recommendations/generate", methods=["POST"])
@login_required
def generate_recommendations():
    """
    API endpoint to generate AI recommendations via Google Gemini.
    Strictly shields against 429 / RESOURCE_EXHAUSTED / timeouts without crashing.
    """
    user_id = session["user_id"]
    user = query_db("SELECT ai_insights_enabled FROM users WHERE id = %s", (user_id,), one=True)
    if user and user.get("ai_insights_enabled") == 0:
        return jsonify({
            "success": False,
            "status_code": 200,
            "is_ai": False,
            "error_type": "disabled_in_settings",
            "message": "AI Insights are currently turned off in your Settings. Please go to Settings and enable 'AI Insights' to generate recommendations.",
            "summary": "",
            "suggestions": "",
            "fallback_available": True,
            "fallback_data": {
                "status": "guidance",
                "title": "AI Insights Disabled in Settings",
                "is_ai": False,
                "summary": "• AI Insights preference is currently toggled OFF in your account Settings.",
                "suggestions": "• Navigate to Settings in the navigation bar.\n• Turn ON the 'AI Insights' toggle switch and click 'Save Settings'.",
                "disclaimer": "You can re-enable AI features anytime from your profile settings page."
            }
        }), 200

    req_json = request.get_json(silent=True) or {}
    simulate_429 = request.args.get("simulate_429", "false").lower() == "true" or \
                   req_json.get("simulate_429") is True
                   
    # Call AI service
    result = get_ai_recommendations(user_id, simulate_429=simulate_429)

    # If successfully generated by Gemini, save to DB
    if result.get("success") and result.get("is_ai"):
        combined_text = f"### AI Spending Summary\n{result.get('summary')}\n\n### Suggested Actions\n{result.get('suggestions')}"
        execute_db(
            "INSERT INTO ai_recommendations (user_id, recommendation_text, source_type) VALUES (%s, %s, %s)",
            (user_id, combined_text, "gemini")
        )
    elif result.get("fallback_available") and result.get("fallback_data"):
        # Save fallback summary if requested or needed
        fb = result["fallback_data"]
        combined_text = f"### {fb['title']}\n{fb['summary']}\n\n### Practical Suggestions\n{fb['suggestions']}"
        execute_db(
            "INSERT INTO ai_recommendations (user_id, recommendation_text, source_type) VALUES (%s, %s, %s)",
            (user_id, combined_text, "basic_fallback")
        )

    return jsonify(result), (200 if result.get("success") or result.get("fallback_available") else result.get("status_code", 400))

# ============================================================
# 8. PROFILE & SETTINGS
# ============================================================

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Displays user profile details and allows editing."""
    user_id = session["user_id"]
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name:
            flash("Full name cannot be empty.", "danger")
            return redirect(url_for("profile"))

        execute_db("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
        session["user_name"] = name

        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters long.", "danger")
                return redirect(url_for("profile"))
            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("profile"))

            pwd_hash = generate_password_hash(new_password, method="scrypt")
            execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (pwd_hash, user_id))
            flash("Profile and password updated successfully!", "success")
        else:
            flash("Profile updated successfully!", "success")

        return redirect(url_for("profile"))

    # Determine auth method
    auth_method = "Google OAuth 2.0" if user.get("google_id") else "Email & Password"

    return render_template("profile.html", user=user, auth_method=auth_method)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """User preferences: Currency, Dark/Light Theme, Notifications, AI toggle."""
    user_id = session["user_id"]
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)

    if request.method == "POST":
        currency = request.form.get("currency", "₹")
        theme = request.form.get("theme", "dark")
        notifications = 1 if request.form.get("notifications") == "on" else 0
        ai_enabled = 1 if request.form.get("ai_insights") == "on" else 0

        execute_db(
            "UPDATE users SET currency = %s, theme = %s, notifications_enabled = %s, ai_insights_enabled = %s WHERE id = %s",
            (currency, theme, notifications, ai_enabled, user_id)
        )
        flash("Settings saved successfully!", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html", user=user)

@app.route("/api/seed-demo-data", methods=["POST"])
@login_required
def populate_demo_data():
    """Seeds sample data (Income: ₹25,000, 5 categorized expenses, budgets, savings goal)."""
    user_id = session["user_id"]
    seed_demo_data(user_id)
    flash("Demo data loaded successfully! Your dashboard is now fully populated.", "success")
    return redirect(url_for("dashboard"))

@app.route("/api/reset-data", methods=["POST"])
@login_required
def reset_data():
    """Clears all financial data for current user."""
    user_id = session["user_id"]
    execute_db("DELETE FROM expenses WHERE user_id = %s", (user_id,))
    execute_db("DELETE FROM budgets WHERE user_id = %s", (user_id,))
    execute_db("DELETE FROM savings_goals WHERE user_id = %s", (user_id,))
    execute_db("DELETE FROM ai_recommendations WHERE user_id = %s", (user_id,))
    execute_db("UPDATE users SET monthly_income = 0 WHERE id = %s", (user_id,))
    flash("All your financial records have been reset.", "info")
    return redirect(url_for("dashboard"))

# ============================================================
# 9. HEALTH CHECK
# ============================================================

@app.route("/health")
def health_check():
    """Production health check endpoint. Returns status ok without exposing secrets."""
    return jsonify({"status": "ok", "app": "PocketSmart AI"}), 200

# ============================================================
# 10. ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", code=404, message="The page you are looking for was not found."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="An internal server error occurred. Our team has been notified."), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
