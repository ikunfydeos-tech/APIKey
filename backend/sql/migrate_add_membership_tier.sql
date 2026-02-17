-- 添加会员等级相关字段到 users 表
-- 适用于 PostgreSQL 数据库

-- 添加会员等级字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS membership_tier VARCHAR(20) DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS membership_expire_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS membership_started_at TIMESTAMP;

-- 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_membership_tier ON users(membership_tier);
CREATE INDEX IF NOT EXISTS idx_users_membership_expire_at ON users(membership_expire_at);

-- 添加注释说明
COMMENT ON COLUMN users.membership_tier IS '会员等级：free(免费版), basic(基础版), pro(专业版)';
COMMENT ON COLUMN users.membership_expire_at IS '会员到期时间，null表示永久或免费版';
COMMENT ON COLUMN users.membership_started_at IS '会员开始时间';