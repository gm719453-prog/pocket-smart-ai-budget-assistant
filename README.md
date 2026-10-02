# 💰 PocketSmart AI – Smart Budget & Recommendation Assistant

PocketSmart AI is a modern, full-stack, AI-powered personal finance and budget assistant designed specifically for college students and beginners. It empowers users to track income, log daily expenses across multiple categories, establish monthly spending limits, visualize cash flows using dynamic charts, monitor savings goals, and receive intelligent, personalized spending advice powered by **Google Gemini AI**.

---

## 🎯 1. College Project Summary (Viva & Review Guide)

### 📌 WHAT is PocketSmart AI?
> **"PocketSmart AI is an AI-powered personal budget and recommendation assistant built for students and beginners."**

### 💡 WHY was it built?
> **"Students and young adults frequently struggle with financial literacy, unmonitored impulse spending, and budget discipline. PocketSmart AI simplifies financial monitoring with automated category calculations and AI-driven insights."**

### ⚙️ HOW does it work?
> **"The application stores expenses, category limits, and savings goals securely in MySQL (with strict user isolation). Spending statistics and budget thresholds are calculated dynamically using Python and Flask, visualized via Chart.js, and summarized into structured advice using Google Gemini."**

---

## 🚀 2. Key Features

- **🛡️ Secure Multi-Method Authentication:**
  - Standard Email/Password registration with `scrypt` cryptographic password hashing.
  - Official Google OAuth 2.0 flow (`Authlib`).
  - Cryptographic token-based password reset (`itsdangerous`).
  - Per-user session protection and data isolation (`user_id` parameterization).
- **💵 Income Management:**
  - Configurable monthly allowance/salary (e.g. ₹25,000) dynamically integrated into dashboard balances.
- **💳 Expense Tracking & CRUD:**
  - Log spending with Amount, Category (`Food`, `Travel`, `Shopping`, `Education`, `Bills`, `Entertainment`, `Health`, `Other`), Description, and Date.
  - Interactive table with real-time search, category filtering, date filters, and sorting.
  - Modal-confirmed expense deletion and updates.
- **📊 Monthly Budget Control & Real-time Alerts:**
  - Set limits per category (e.g. Food: ₹5,000, Travel: ₹3,000).
  - Real-time progress bars with dynamic status indicators:
    - 🟢 Normal (< 85% spent)
    - 🟡 Warning (≥ 85% spent): *"You're getting close to your [Category] budget."*
    - 🔴 Exceeded (≥ 100% spent): *"Your [Category] budget has been exceeded!"*
- **🎯 Milestone Savings Goals:**
  - Create targets (e.g., "New Laptop" target ₹50,000).
  - Quick deposit / "+ Add Funds" action with live progress percentage.
- **📈 Dynamic Visual Analytics (Chart.js):**
  - Category Doughnut Chart.
  - Monthly Spending Trajectory (historical comparisons).
  - Budget vs Actual Spending Comparison.
- **🤖 Google Gemini AI Insights with Robust 429 Shielding:**
  - Generates spending proportion analysis, highest expenditure flags, and actionable next-month tips.
  - **Graceful Error Handling:** Gracefully handles `HTTP 429`, `RESOURCE_EXHAUSTED`, quota exhaustion, and timeouts without crashing the app.
  - **Offline/Fallback Summary:** Generates a deterministic *"Basic spending summary"* calculated locally using Python if Gemini is offline or rate-limited.
  - **Viva Review Mode:** Built-in *"Simulate 429"* button to demonstrate quota shielding live during evaluations.
- **🎨 Modern Glassmorphic UI:**
  - Ambient glowing gradients, count-up animations (₹0 → ₹25,000), dark/light theme switch, mobile-responsive layout.

---

## 🛠️ 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Vanilla design system), JavaScript (ES6+), Bootstrap 5, Chart.js, Font Awesome 6 |
| **Backend** | Python 3.10+, Flask |
| **Database** | MySQL 8.0+ (with automatic local SQLite fallback if MySQL is unconfigured) |
| **AI Engine** | Google Gemini API (`google-generativeai`) |
| **Auth** | Werkzeug Security (`scrypt`), Authlib (Google OAuth 2.0) |
| **Config** | python-dotenv |

---

## 📂 4. Project Structure

```text
PocketSmart/
│
├── app.py                  # Main Flask application & routes
├── config.py               # Environment configuration loader
├── database.py             # Reusable MySQL connection logic & auto-init
├── auth.py                 # Authentication helpers & Google OAuth
├── ai_service.py           # Gemini AI integration, 429 shielding & fallback
├── requirements.txt        # Python dependency manifest
├── .env                    # Environment secrets (ignored in Git)
├── .env.example            # Sample configuration template
├── .gitignore              # Git ignore rules
├── README.md               # Complete project documentation
│
├── database/
│   └── schema.sql          # MySQL database schema DDL
│
├── templates/
│   ├── base.html           # Master layout with sidebar & topbar
│   ├── index.html          # Modern animated landing page
│   ├── login.html          # User login (Email & Google OAuth)
│   ├── signup.html         # User registration with validation
│   ├── forgot_password.html# Password reset request
│   ├── reset_password.html # New password entry form
│   ├── dashboard.html      # 6 Metric cards, charts & recent items
│   ├── income.html         # Monthly income management
│   ├── expenses.html       # Expense history, search & filter
│   ├── add_expense.html    # Record new expense
│   ├── edit_expense.html   # Modify existing expense
│   ├── budget.html         # Category budget thresholds & warnings
│   ├── recommendations.html# Gemini AI spending insights
│   ├── savings.html        # Milestone savings goals
│   ├── profile.html        # User profile & credentials
│   ├── settings.html       # Preferences, currency & demo data
│   └── error.html          # Friendly 404 & 500 error display
│
└── static/
    ├── css/
    │   ├── style.css       # Core design system & animations
    │   ├── auth.css        # Authentication styling
    │   └── dashboard.css   # Dashboard layout & tables
    ├── js/
    │   ├── app.js          # Theme toggle & global toasts
    │   ├── auth.js         # Show/hide password & validation
    │   ├── dashboard.js    # Count-up number animation
    │   ├── expenses.js     # Search filter & delete modal
    │   └── charts.js       # Chart.js visualizations
    └── images/
        ├── logo.svg        # PocketSmart AI brand logo
        └── default-avatar.svg # Default profile image
```

---

## ⚙️ 5. Installation & Setup Guide

### Step 1: Clone or Navigate to the Project
```bash
cd "pocketSmart Ai Budget assistant"
```

### Step 2: Create and Activate a Python Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure `.env` File
Create a `.env` file from `.env.example`:
```env
SECRET_KEY=pocketsmart_super_secure_secret_key_change_in_production_2026

# MySQL Database Settings
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=pocketsmart

# Google Gemini API Key (From Google AI Studio: https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# Google OAuth 2.0 Credentials (Optional, for Google Sign-in)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

PORT=5000
FLASK_DEBUG=True
```

### Step 5: Initialize MySQL Database (Optional)
If running standard MySQL, execute the schema:
```bash
mysql -u root -p < database/schema.sql
```
> **Note on Portability:** `database.py` contains auto-initialization logic. If MySQL is not running on your presentation machine, the application will automatically fall back to an internal SQLite engine without throwing errors, ensuring smooth college viva demonstrations anywhere!

---

## 🏃 6. Running the Application Locally

Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000/
```

---

## ☁️ 6.1 Vercel Production Deployment Guide

Follow these exact steps to deploy the application to Vercel:

1. **Push latest code to GitHub:**
   ```bash
   git add .
   git commit -m "prep: vercel deployment configuration"
   git push origin master
   ```
2. **Open Vercel:** Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
3. **Import Repository:** Click **Add New... -> Project** and select `pocket-smart-ai-budget-assistant`.
4. **Select Project Settings:** Vercel automatically detects [`vercel.json`](file:///c:/Users/sathi/OneDrive/Desktop/pocketSmart%20Ai%20Budget%20assistant/vercel.json) and uses `@vercel/python`.
5. **Configure Environment Variables:** Add the following in Vercel's Environment Variables tab:
   - `SECRET_KEY` = `(your random secret key)`
   - `GEMINI_API_KEY` = `(your Gemini API key)`
   - `GOOGLE_CLIENT_ID` = `(your Google OAuth Client ID)`
   - `GOOGLE_CLIENT_SECRET` = `(your Google OAuth Client Secret)`
   - `DB_HOST` = `(your cloud MySQL database host)`
   - `DB_PORT` = `3306`
   - `DB_USER` = `(your cloud MySQL username)`
   - `DB_PASSWORD` = `(your cloud MySQL password)`
   - `DB_NAME` = `pocketsmart`
   - `SESSION_COOKIE_SECURE` = `True`
6. **Configure Production Database:** Initialize tables on your cloud MySQL database using [`database/schema.sql`](file:///c:/Users/sathi/OneDrive/Desktop/pocketSmart%20Ai%20Budget%20assistant/database/schema.sql).
7. **Deploy:** Click **Deploy**. Vercel will build and launch your application.
8. **Open Deployed URL:** Access your live URL (e.g., `https://pocket-smart-ai-budget-assistant.vercel.app`).
9. **Test `/health`:** Verify `https://your-domain.vercel.app/health` returns `{"app": "PocketSmart AI", "status": "ok"}`.
10. **Test Login & Signup:** Register a test account or log in with credentials.
11. **Test Dashboard:** Verify balances, metric cards, and Chart.js graphs render.
12. **Test Expenses:** Log a transaction and test search, filtering, and deletion.
13. **Test Budget:** Add category limits and verify status progress bars.
14. **Test Savings:** Create a goal and deposit funds.
15. **Test AI Insights:** Generate AI recommendations via Gemini and test rate-limit fallback.
16. **Configure Google OAuth Redirect URI:** Add `https://your-domain.vercel.app/auth/google/callback` under Authorized Redirect URIs in Google Cloud Console.

---

## 🧪 7. Review & Testing Checklist

| Test Item | Expected Result | Verified |
| :--- | :--- | :---: |
| **Landing Page** | Animated hero, feature cards, and direct links to Login/Signup | ✅ |
| **Email Sign-Up** | Hashes password with `scrypt`, validates email, creates user | ✅ |
| **Login Flow** | Protects session; rejects invalid credentials with generic error | ✅ |
| **One-Click Demo** | Click *"Load Demo Data"* in Dashboard or Settings to populate ₹25,000 income, expenses & budgets | ✅ |
| **Budget Limit Alert** | Exceeding a budget shows prominent warning/danger banners | ✅ |
| **Chart Visualizations**| Chart.js renders Category Doughnut, Monthly Trend & Budget Comparisons | ✅ |
| **Gemini AI Insights** | Analyzes summarized numbers into Structured Summary & Suggestions | ✅ |
| **Gemini 429 Test** | Click *"Simulate 429"* on AI Insights page: Shows friendly *"AI temporarily unavailable"* message + Local Fallback summary without crashing! | ✅ |
| **User Isolation** | Each user sees strictly their own financial records | ✅ |

---

## 🛡️ 8. Security Highlights

1. **Parameterized Queries:** All SQL queries use `%s` (or `?` parameterization), preventing SQL Injection.
2. **Password Hashing:** `werkzeug.security.generate_password_hash` (`scrypt`) ensures plain-text passwords are never stored.
3. **Session Cookies:** `HTTPOnly` and `SameSite='Lax'` prevent client-side script tampering.
4. **Data Minimization:** Only aggregated financial totals (income, expenses, category sums) are forwarded to Gemini; credentials and personal identifiers are strictly excluded.
5. **Sanitized Error Surfaces:** No raw stack traces, API keys, or Trajectory/Trace IDs are ever exposed to the user.

---

## 👨‍🎓 9. College Project Presentation Script

When demonstrating this project to professors or examiners:
1. **Introduction:** Show the **Landing Page** with modern responsive animations.
2. **Authentication:** Log in using your email account or click **Continue with Google**.
3. **Dashboard:** Highlight the 6 metric cards with smooth count-up animations, the category doughnut chart, and real-time budget alert banners.
4. **CRUD Actions:** Add a new expense (e.g. ₹600 in *Food*) and show how the remaining budget and charts update dynamically.
5. **AI Feature & 429 Demonstration:** Navigate to **AI Insights**, click **Generate AI Insights** to showcase Gemini's natural language analysis. Then click **Simulate 429** to demonstrate that the application handles API rate limits gracefully with friendly messages and a local fallback summary without crashing.

---

## 📄 License
This project is open-source and developed for academic review and student portfolio purposes.
