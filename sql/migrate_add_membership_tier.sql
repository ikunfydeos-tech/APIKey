-- 为用户表添加会员相关字段
-- 执行时间: 2026-02-18

-- 添加会员等级字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS membership_tier VARCHAR(20) DEFAULT 'free';

-- 添加会员到期时间字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS membership_expire_at TIMESTAMP DEFAULT NULL;

-- 添加会员开始时间字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS membership_started_at TIMESTAMP DEFAULT NULL;

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_membership_tier ON users(membership_tier);
CREATE INDEX IF NOT EXISTS idx_users_membership_expire_at ON users(membership_expire_at);

-- 添加注释
COMMENT ON COLUMN users.membership_tier IS '会员等级: free(免费版), basic(基础版), pro(专业版)';
COMMENT ON COLUMN users.membership_expire_at IS '会员到期时间，NULL表示免费版';
COMMENT ON COLUMN users.membership_started_at IS '会员开始时间';

-- 验证结果
SELECT id, username, email, role, membership_tier, membership_expire_at, membership_started_at FROM users ORDER BY id;
