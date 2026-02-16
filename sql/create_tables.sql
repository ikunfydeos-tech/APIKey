-- API Providers Table
CREATE TABLE IF NOT EXISTS api_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    base_url VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User API Keys Table
CREATE TABLE IF NOT EXISTS user_api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider_id INTEGER REFERENCES api_providers(id) ON DELETE SET NULL,
    key_name VARCHAR(100) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_key_preview VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'expired')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    CONSTRAINT unique_user_key_name UNIQUE (user_id, key_name)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON user_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_provider_id ON user_api_keys(provider_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_status ON user_api_keys(status);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-update timestamps
DROP TRIGGER IF EXISTS update_api_providers_updated_at ON api_providers;
CREATE TRIGGER update_api_providers_updated_at
    BEFORE UPDATE ON api_providers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_api_keys_updated_at ON user_api_keys;
CREATE TRIGGER update_user_api_keys_updated_at
    BEFORE UPDATE ON user_api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert preset API providers
INSERT INTO api_providers (name, display_name, base_url, description, icon, sort_order) VALUES
('openai', 'OpenAI', 'https://api.openai.com/v1', 'OpenAI GPT models API', 'openai', 1),
('anthropic', 'Anthropic', 'https://api.anthropic.com/v1', 'Claude models API', 'anthropic', 2),
('google', 'Google AI', 'https://generativelanguage.googleapis.com/v1', 'Google Gemini models API', 'google', 3),
('azure', 'Azure OpenAI', 'https://YOUR_RESOURCE.openai.azure.com', 'Microsoft Azure OpenAI Service', 'azure', 4),
('deepseek', 'DeepSeek', 'https://api.deepseek.com/v1', 'DeepSeek AI models API', 'deepseek', 5),
('moonshot', 'Moonshot', 'https://api.moonshot.cn/v1', 'Moonshot Kimi models API', 'moonshot', 6),
('zhipu', 'Zhipu AI', 'https://open.bigmodel.cn/api/paas/v4', 'Zhipu GLM models API', 'zhipu', 7),
('baidu', 'Baidu Wenxin', 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1', 'Baidu ERNIE models API', 'baidu', 8),
('alibaba', 'Alibaba Tongyi', 'https://dashscope.aliyuncs.com/api/v1', 'Alibaba Qwen models API', 'alibaba', 9)
ON CONFLICT (name) DO NOTHING;

-- API Models Table
CREATE TABLE IF NOT EXISTS api_models (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES api_providers(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(100),
    category VARCHAR(50) DEFAULT 'chat',
    context_window VARCHAR(20),
    is_default BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, model_id)
);

-- Create index for category queries
CREATE INDEX IF NOT EXISTS idx_api_models_category ON api_models(category);

-- Add model_id column to user_api_keys
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_api_keys' AND column_name = 'model_id'
    ) THEN
        ALTER TABLE user_api_keys ADD COLUMN model_id VARCHAR(100);
    END IF;
END $$;

-- Insert preset models with categories
-- Categories: chat, code, long_context, economy, vision
INSERT INTO api_models (provider_id, model_id, model_name, category, context_window, is_default, sort_order) VALUES
-- OpenAI models
(1, 'gpt-4o', 'GPT-4o', 'chat', '128K', true, 1),
(1, 'gpt-4o-mini', 'GPT-4o Mini', 'economy', '128K', false, 2),
(1, 'gpt-4-turbo', 'GPT-4 Turbo', 'chat', '128K', false, 3),
(1, 'gpt-4', 'GPT-4', 'chat', '8K', false, 4),
(1, 'gpt-3.5-turbo', 'GPT-3.5 Turbo', 'economy', '16K', false, 5),
(1, 'gpt-4-vision-preview', 'GPT-4 Vision', 'vision', '128K', false, 6),
(1, 'o1', 'o1', 'chat', '200K', false, 10),
(1, 'o1-mini', 'o1 Mini', 'chat', '128K', false, 11),
-- Anthropic models
(2, 'claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', 'chat', '200K', true, 1),
(2, 'claude-3-opus-20240229', 'Claude 3 Opus', 'chat', '200K', false, 2),
(2, 'claude-3-haiku-20240307', 'Claude 3 Haiku', 'economy', '200K', false, 3),
(2, 'claude-3-5-sonnet', 'Claude 3.5 Sonnet (Latest)', 'vision', '200K', false, 4),
-- Google AI models
(3, 'gemini-1.5-pro', 'Gemini 1.5 Pro', 'long_context', '2M', true, 1),
(3, 'gemini-1.5-flash', 'Gemini 1.5 Flash', 'economy', '1M', false, 2),
(3, 'gemini-pro', 'Gemini Pro', 'chat', '32K', false, 3),
(3, 'gemini-2.0-flash', 'Gemini 2.0 Flash', 'vision', '1M', false, 4),
(3, 'gemini-1.5-pro-latest', 'Gemini 1.5 Pro (Latest)', 'vision', '2M', false, 5),
-- DeepSeek models
(5, 'deepseek-chat', 'DeepSeek Chat', 'chat', '64K', true, 1),
(5, 'deepseek-coder', 'DeepSeek Coder', 'code', '64K', false, 2),
-- Moonshot models
(6, 'moonshot-v1-8k', 'Moonshot V1 8K', 'chat', '8K', true, 1),
(6, 'moonshot-v1-32k', 'Moonshot V1 32K', 'long_context', '32K', false, 2),
(6, 'moonshot-v1-128k', 'Moonshot V1 128K', 'long_context', '128K', false, 3),
-- Zhipu AI models
(7, 'glm-4', 'GLM-4', 'chat', '128K', true, 1),
(7, 'glm-4-flash', 'GLM-4 Flash', 'economy', '128K', false, 2),
(7, 'glm-4-plus', 'GLM-4 Plus', 'chat', '128K', false, 3),
(7, 'glm-4-air', 'GLM-4 Air', 'economy', '128K', false, 4),
-- Baidu models
(8, 'ernie-4.0-8k', 'ERNIE 4.0', 'chat', '8K', true, 1),
(8, 'ernie-3.5-8k', 'ERNIE 3.5', 'economy', '8K', false, 2),
(8, 'ernie-speed-8k', 'ERNIE Speed', 'economy', '8K', false, 3),
-- Alibaba models
(9, 'qwen-turbo', 'Qwen Turbo', 'economy', '8K', true, 1),
(9, 'qwen-plus', 'Qwen Plus', 'chat', '32K', false, 2),
(9, 'qwen-max', 'Qwen Max', 'chat', '32K', false, 3),
(9, 'qwen-long', 'Qwen Long', 'long_context', '10M', false, 4)
ON CONFLICT (provider_id, model_id) DO NOTHING;
