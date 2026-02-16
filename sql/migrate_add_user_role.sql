-- 为用户表添加 role 字段，用于区分管理员和普通用户
-- 执行时间: 2026-02-15

-- 添加 role 字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 将第一个用户设置为管理员（可选，根据实际需求调整）
-- UPDATE users SET role = 'admin' WHERE id = 1;

-- 验证结果
SELECT id, username, email, role FROM users ORDER BY id;
