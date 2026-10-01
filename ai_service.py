import os
import logging
import time
from config import Config

logger = logging.getLogger("pocketsmart.ai_service")

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------
# SDK Import — uses the current google-genai SDK (v2+)
# Falls back gracefully if the package is missing.
# ---------------------------------------------------------------
try:
    from google import genai
    from google.genai import types as genai_types
    GENAI_AVAILABLE = True
    logger.info("google-genai SDK loaded successfully.")
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai package is not installed. Run: pip install google-genai")

# Configurable model — override with GEMINI_MODEL env var if needed
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def build_spending_summary_data(user_id):
    """
    Summarizes user financial data securely for AI analysis.
    Only aggregated numbers are gathered; no credentials or sensitive tokens.
    """
    from datetime import date
    from database import query_db

    today = date.today()
    current_month = today.strftime("%Y-%m")

    # 1. User monthly income and currency
    user = query_db("SELECT monthly_income, currency FROM users WHERE id = %s", (user_id,), one=True)
    income = float(user["monthly_income"] or 0.0) if user else 0.0
    currency = (user.get("currency") if user else None) or "₹"

    # 2. Total expenses and category breakdown for current month
    month_pattern = f"{current_month}%"
    category_expenses = query_db(
        "SELECT category, SUM(amount) as total FROM expenses "
        "WHERE user_id = %s AND expense_date LIKE %s "
        "GROUP BY category ORDER BY total DESC",
        (user_id, month_pattern)
    )

    cat_breakdown = {row["category"]: float(row["total"]) for row in category_expenses}
    total_expenses = sum(cat_breakdown.values())

    # 3. Monthly budgets
    budgets = query_db(
        "SELECT category, budget_amount FROM budgets "
        "WHERE user_id = %s AND month = %s",
        (user_id, current_month)
    )
    cat_budgets = {b["category"]: float(b["budget_amount"]) for b in budgets}
    total_budget = sum(cat_budgets.values())

    # 4. Savings goals
    savings = query_db(
        "SELECT goal_name, target_amount, saved_amount FROM savings_goals "
        "WHERE user_id = %s",
        (user_id,)
    )
    savings_list = []
    for s in savings:
        target = float(s["target_amount"] or 0)
        saved = float(s["saved_amount"] or 0)
        pct = round((saved / target * 100), 1) if target > 0 else 0
        savings_list.append({
            "goal": s["goal_name"],
            "target": target,
            "saved": saved,
            "percent": pct
        })

    return {
        "month": current_month,
        "currency": currency,
        "income": income,
        "total_budget": total_budget,
        "category_budgets": cat_budgets,
        "total_expenses": total_expenses,
        "category_expenses": cat_breakdown,
        "savings_goals": savings_list
    }


def generate_local_fallback_summary(data):
    """
    Generates a basic, deterministic spending summary locally in Python.
    Clearly labeled as 'Basic spending summary' (NOT AI).
    Works 100% offline even when Gemini API is rate-limited or unavailable.
    """
    currency = data.get("currency", "₹")
    total_exp = data.get("total_expenses", 0.0)
    income = data.get("income", 0.0)
    cat_exp = data.get("category_expenses", {})
    cat_budgets = data.get("category_budgets", {})
    savings = data.get("savings_goals", [])

    highest_cat = "None"
    highest_amt = 0.0
    for cat, amt in cat_exp.items():
        if amt > highest_amt:
            highest_amt = amt
            highest_cat = cat

    summary_lines = []
    summary_lines.append(f"• Total recorded spending this month is {currency}{total_exp:,.2f}.")

    if income > 0:
        pct_of_income = round((total_exp / income) * 100, 1)
        remaining_income = income - total_exp
        summary_lines.append(
            f"• Recorded spending accounts for {pct_of_income}% of your monthly income "
            f"({currency}{income:,.2f}). Remaining balance is {currency}{remaining_income:,.2f}."
        )
    else:
        summary_lines.append(
            "• Monthly income is not yet configured. Set your income in the Income section for budget ratio analysis."
        )

    if highest_amt > 0:
        summary_lines.append(f"• Highest spending category is {highest_cat} with {currency}{highest_amt:,.2f} recorded.")
    else:
        summary_lines.append("• No expense records found for this month yet.")

    # Budget overages
    over_budget = []
    for cat, spent in cat_exp.items():
        if cat in cat_budgets:
            limit = cat_budgets[cat]
            if spent > limit:
                over_budget.append(f"{cat} (exceeded by {currency}{spent - limit:,.2f})")

    if over_budget:
        summary_lines.append(f"• Budget alert: Exceeded limits in: {', '.join(over_budget)}.")
    elif cat_budgets:
        summary_lines.append("• Good discipline: All tracked categories are currently within assigned budgets.")

    if savings:
        g_info = [f"{g['goal']} ({g['percent']}% completed)" for g in savings[:2]]
        summary_lines.append(f"• Active savings goals: {', '.join(g_info)}.")

    suggestions = [
        "Review your highest spending category to identify flexible or discretionary purchases.",
        "Consider allocating surplus funds from remaining monthly income directly toward your active savings goals.",
        "Keep logging daily transactions to maintain real-time accuracy across all spending categories."
    ]

    return {
        "status": "fallback",
        "title": "Basic spending summary",
        "is_ai": False,
        "summary": "\n".join(summary_lines),
        "suggestions": "\n".join(f"• {s}" for s in suggestions),
        "disclaimer": "This is a basic spending summary calculated locally from your recorded figures. AI insights will resume once the service is available."
    }


def get_ai_recommendations(user_id, simulate_429=False):
    """
    Main function to get AI recommendations using Google Gemini (google-genai SDK v2+).
    Provides strict 429/ResourceExhausted handling, retry limits, and local fallback.

    Returns a dict with keys:
        success, status_code, is_ai, error_type, message,
        summary, suggestions, fallback_available, fallback_data
    """
    # ---------------------------------------------------------------
    # Simulation mode for college viva / testing
    # ---------------------------------------------------------------
    if simulate_429:
        logger.info("Simulating HTTP 429 (RESOURCE_EXHAUSTED) for verification testing.")
        return {
            "success": False,
            "status_code": 429,
            "is_ai": False,
            "error_type": "rate_limit",
            "message": "🤖 AI recommendations are temporarily unavailable.\n\nPlease try again after a few minutes.",
            "summary": "",
            "suggestions": "",
            "fallback_available": True,
            "fallback_data": generate_local_fallback_summary(build_spending_summary_data(user_id))
        }

    # ---------------------------------------------------------------
    # Fetch summarized financial data (aggregates only — no secrets)
    # ---------------------------------------------------------------
    data = build_spending_summary_data(user_id)

    # Require at least some financial data before calling AI
    if data["total_expenses"] == 0 and data["income"] == 0:
        return {
            "success": False,
            "status_code": 400,
            "is_ai": False,
            "error_type": "insufficient_data",
            "message": "Add some expenses or set your monthly income first to receive AI insights.",
            "summary": "",
            "suggestions": "",
            "fallback_available": False,
            "fallback_data": None
        }

    # ---------------------------------------------------------------
    # API key check — log warning but never expose the key value
    # ---------------------------------------------------------------
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        logger.warning("GEMINI_API_KEY is not configured in environment variables.")
        return {
            "success": False,
            "status_code": 401,
            "is_ai": False,
            "error_type": "missing_api_key",
            "message": "AI service is not configured. Please add your GEMINI_API_KEY to the .env file.",
            "summary": "",
            "suggestions": "",
            "fallback_available": True,
            "fallback_data": generate_local_fallback_summary(data)
        }

    # ---------------------------------------------------------------
    # SDK availability check
    # ---------------------------------------------------------------
    if not GENAI_AVAILABLE:
        logger.warning("google-genai SDK is not installed. Run: pip install google-genai")
        return {
            "success": False,
            "status_code": 500,
            "is_ai": False,
            "error_type": "module_missing",
            "message": "AI service is temporarily unavailable. Please try again later.",
            "summary": "",
            "suggestions": "",
            "fallback_available": True,
            "fallback_data": generate_local_fallback_summary(data)
        }

    # ---------------------------------------------------------------
    # Build privacy-preserving prompt (aggregated numbers only)
    # ---------------------------------------------------------------
    currency = data["currency"]
    prompt = f"""You are PocketSmart AI, a helpful, polite, and practical college budget assistant.
Analyze the following summarized user financial numbers for the current month ({data['month']}):

FINANCIAL SUMMARY:
- Monthly Income: {currency}{data['income']:,.2f}
- Total Budget Assigned: {currency}{data['total_budget']:,.2f}
- Category Budgets: {data['category_budgets']}
- Total Expenses Recorded: {currency}{data['total_expenses']:,.2f}
- Spending by Category: {data['category_expenses']}
- Savings Goals: {data['savings_goals']}

STRICT INSTRUCTIONS:
1. Base your insights ONLY on the exact data provided above.
2. DO NOT invent or assume any extra transactions, income, or savings.
3. If an item is missing or zero, note it simply and politely.
4. Structure your response in EXACTLY TWO sections formatted with clean markdown bullets:

### AI Spending Summary
(Provide concise bullet points summarizing spending proportion, highest categories, and budget status.)

### Suggested Actions
(Provide 3 to 4 actionable, practical steps for student financial wellness and next-month planning.)

Keep the tone encouraging, objective, and beginner-friendly."""

    # ---------------------------------------------------------------
    # Call Gemini API — google-genai SDK v2+ style
    # ---------------------------------------------------------------
    try:
        client = genai.Client(api_key=api_key)

        logger.info(f"Calling Gemini model: {GEMINI_MODEL}")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        # Extract text from response
        if not response or not response.text:
            raise ValueError("Empty response received from Gemini API.")

        full_text = response.text.strip()
        logger.info("Gemini response received successfully.")

        # ---------------------------------------------------------------
        # Parse response into summary + suggestions sections
        # ---------------------------------------------------------------
        summary_part = ""
        suggestions_part = ""

        if "### Suggested Actions" in full_text:
            parts = full_text.split("### Suggested Actions")
            summary_part = parts[0].replace("### AI Spending Summary", "").strip()
            suggestions_part = parts[1].strip()
        elif "Suggested Actions" in full_text:
            parts = full_text.split("Suggested Actions")
            summary_part = parts[0].replace("AI Spending Summary", "").strip()
            suggestions_part = parts[1].strip()
        else:
            summary_part = full_text
            suggestions_part = "Review discretionary categories and continue setting aside monthly savings."

        return {
            "success": True,
            "status_code": 200,
            "is_ai": True,
            "error_type": None,
            "message": "AI insights generated successfully.",
            "summary": summary_part,
            "suggestions": suggestions_part,
            "disclaimer": "AI suggestions are for general informational purposes and are not professional financial advice.",
            "fallback_available": False,
            "fallback_data": None
        }

    except Exception as exc:
        err_str = str(exc)
        err_lower = err_str.lower()

        # Log full technical error to backend console — never to user
        logger.error(f"Gemini AI Error: {err_str}", exc_info=True)

        # ---------------------------------------------------------------
        # Categorize error without leaking internals to the UI
        # ---------------------------------------------------------------
        if any(term in err_lower for term in ["429", "resource_exhausted", "quota", "rate limit", "ratelimit", "too many requests"]):
            friendly_message = "🤖 AI recommendations are temporarily unavailable.\n\nPlease try again after a few minutes."
            status_code = 429
            error_type = "rate_limit"
        elif any(term in err_lower for term in ["401", "403", "unauthenticated", "permissiondenied", "api_key_invalid", "invalid api key", "api key not valid"]):
            friendly_message = "AI service configuration needs attention. Please check your GEMINI_API_KEY."
            status_code = 403
            error_type = "auth_error"
        elif any(term in err_lower for term in ["timeout", "deadlineexceeded", "timed out"]):
            friendly_message = "The AI request took too long. Please try again."
            status_code = 504
            error_type = "timeout"
        elif any(term in err_lower for term in ["500", "503", "unavailable", "server error", "internal error"]):
            friendly_message = "AI service is temporarily unavailable. Please try again later."
            status_code = 503
            error_type = "server_error"
        elif any(term in err_lower for term in ["connection", "network", "dns", "failed to resolve", "could not connect"]):
            friendly_message = "Unable to connect to the AI service. Please check your internet connection."
            status_code = 502
            error_type = "network_error"
        elif any(term in err_lower for term in ["not found", "404", "model", "does not exist"]):
            friendly_message = "AI model is temporarily unavailable. Please try again later."
            status_code = 404
            error_type = "model_error"
        else:
            friendly_message = "AI recommendations are temporarily unavailable. Please try again later."
            status_code = 500
            error_type = "unknown_error"

        return {
            "success": False,
            "status_code": status_code,
            "is_ai": False,
            "error_type": error_type,
            "message": friendly_message,
            "summary": "",
            "suggestions": "",
            "fallback_available": True,
            "fallback_data": generate_local_fallback_summary(data)
        }
