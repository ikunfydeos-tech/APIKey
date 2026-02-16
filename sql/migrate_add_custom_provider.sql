-- 迁移脚本：添加自定义服务商支持
-- 执行日期：2026-02-15

-- 1. api_providers 表添加字段
ALTER TABLE api_providers ADD COLUMN IF NOT EXISTS is_custom BOOLEAN DEFAULT FALSE;
ALTER TABLE api_providers ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);

-- 2. 为自定义服务商创建索引
CREATE INDEX IF NOT EXISTS idx_api_providers_is_custom ON api_providers(is_custom);
CREATE INDEX IF NOT EXISTS idx_api_providers_created_by ON api_providers(created_by);

-- 3. 更新"自定义"服务商为自定义类型（id=10）
UPDATE api_providers SET is_custom = TRUE WHERE name = 'custom';

-- 4. 注释
COMMENT ON COLUMN api_providers.is_custom IS '是否为用户自定义服务商';
COMMENT ON COLUMN api_providers.created_by IS '创建该服务商的用户ID（仅自定义服务商）';
