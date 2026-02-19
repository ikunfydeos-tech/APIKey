-- 用户余额表
CREATE TABLE IF NOT EXISTS user_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    balance REAL DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES api_providers(id) ON DELETE CASCADE
);

-- API调用记录表
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    api_key_id INTEGER,
    provider_id INTEGER,
    model_id VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    cost REAL DEFAULT 0,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (api_key_id) REFERENCES user_api_keys(id) ON DELETE SET NULL
);

-- 会员续费记录表
CREATE TABLE IF NOT EXISTS subscription_renewals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subscription_type VARCHAR(20),
    amount REAL,
    payment_method VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户余额变更历史表
CREATE TABLE IF NOT EXISTS balance_change_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    balance_type VARCHAR(20), -- topup, deduction, expiration
    amount REAL,
    balance_before REAL,
    balance_after REAL,
    reference_id INTEGER,
    reference_type VARCHAR(50),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- IP地理位置记录表
CREATE TABLE IF NOT EXISTS ip_location_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    location VARCHAR(200),
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    latitude REAL,
    longitude REAL,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 添加会员过期时间索引
CREATE INDEX IF NOT EXISTS idx_users_membership_expire_at ON users(membership_expire_at);
CREATE INDEX IF NOT EXISTS idx_user_balances_user_id ON user_balances(user_id);
CREATE INDEX IF NOT EXISTS idx_user_balances_provider_id ON user_balances(provider_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_user_id ON api_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_created_at ON api_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_subscription_renewals_user_id ON subscription_renewals(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_renewals_created_at ON subscription_renewals(created_at);
CREATE INDEX IF NOT EXISTS idx_balance_change_logs_user_id ON balance_change_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_balance_change_logs_created_at ON balance_change_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_ip_location_records_user_id ON ip_location_records(user_id);
CREATE INDEX IF NOT EXISTS idx_ip_location_records_ip_address ON ip_location_records(ip_address);