-- ============================================================
-- PocketSmart AI – Database Schema
-- MySQL 8.0+ Compatible
-- ============================================================

CREATE DATABASE IF NOT EXISTS pocketsmart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE pocketsmart;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(191) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NULL,
    google_id VARCHAR(100) NULL UNIQUE,
    profile_image VARCHAR(255) DEFAULT '/static/images/default-avatar.svg',
    monthly_income DECIMAL(12, 2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT '₹',
    theme VARCHAR(20) DEFAULT 'dark',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    ai_insights_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. EXPENSES TABLE
CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL,
    expense_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, expense_date),
    INDEX idx_user_category (user_id, category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. BUDGET TABLE
CREATE TABLE IF NOT EXISTS budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    budget_amount DECIMAL(12, 2) NOT NULL,
    month VARCHAR(7) NOT NULL, -- Format: YYYY-MM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_cat_month (user_id, category, month),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_month (user_id, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. SAVINGS GOALS TABLE
CREATE TABLE IF NOT EXISTS savings_goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    goal_name VARCHAR(100) NOT NULL,
    target_amount DECIMAL(12, 2) NOT NULL,
    saved_amount DECIMAL(12, 2) DEFAULT 0.00,
    target_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_savings (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. AI RECOMMENDATIONS TABLE
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recommendation_text MEDIUMTEXT NOT NULL,
    source_type VARCHAR(20) DEFAULT 'gemini', -- 'gemini' or 'basic_fallback'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_rec (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. PASSWORD RESETS TABLE
CREATE TABLE IF NOT EXISTS password_resets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
