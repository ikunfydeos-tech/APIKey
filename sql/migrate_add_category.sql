-- Migration: Add category and context_window to api_models
-- Date: 2026-02-15

-- Add category column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'api_models' AND column_name = 'category'
    ) THEN
        ALTER TABLE api_models ADD COLUMN category VARCHAR(50) DEFAULT 'chat';
    END IF;
END $$;

-- Add context_window column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'api_models' AND column_name = 'context_window'
    ) THEN
        ALTER TABLE api_models ADD COLUMN context_window VARCHAR(20);
    END IF;
END $$;

-- Update existing models with category and context_window
-- OpenAI models
UPDATE api_models SET category = 'chat', context_window = '128K' WHERE model_id = 'gpt-4o';
UPDATE api_models SET category = 'economy', context_window = '128K' WHERE model_id = 'gpt-4o-mini';
UPDATE api_models SET category = 'chat', context_window = '128K' WHERE model_id = 'gpt-4-turbo';
UPDATE api_models SET category = 'chat', context_window = '8K' WHERE model_id = 'gpt-4';
UPDATE api_models SET category = 'economy', context_window = '16K' WHERE model_id = 'gpt-3.5-turbo';

-- Anthropic models
UPDATE api_models SET category = 'chat', context_window = '200K' WHERE model_id = 'claude-3-5-sonnet-20241022';
UPDATE api_models SET category = 'chat', context_window = '200K' WHERE model_id = 'claude-3-opus-20240229';
UPDATE api_models SET category = 'economy', context_window = '200K' WHERE model_id = 'claude-3-haiku-20240307';

-- Google AI models
UPDATE api_models SET category = 'long_context', context_window = '2M' WHERE model_id = 'gemini-1.5-pro';
UPDATE api_models SET category = 'economy', context_window = '1M' WHERE model_id = 'gemini-1.5-flash';
UPDATE api_models SET category = 'chat', context_window = '32K' WHERE model_id = 'gemini-pro';

-- DeepSeek models
UPDATE api_models SET category = 'chat', context_window = '64K' WHERE model_id = 'deepseek-chat';
UPDATE api_models SET category = 'code', context_window = '64K' WHERE model_id = 'deepseek-coder';

-- Moonshot models
UPDATE api_models SET category = 'chat', context_window = '8K' WHERE model_id = 'moonshot-v1-8k';
UPDATE api_models SET category = 'long_context', context_window = '32K' WHERE model_id = 'moonshot-v1-32k';
UPDATE api_models SET category = 'long_context', context_window = '128K' WHERE model_id = 'moonshot-v1-128k';

-- Zhipu AI models
UPDATE api_models SET category = 'chat', context_window = '128K' WHERE model_id = 'glm-4';
UPDATE api_models SET category = 'economy', context_window = '128K' WHERE model_id = 'glm-4-flash';
UPDATE api_models SET category = 'chat', context_window = '128K' WHERE model_id = 'glm-4-plus';
UPDATE api_models SET category = 'economy', context_window = '128K' WHERE model_id = 'glm-4-air';

-- Baidu models
UPDATE api_models SET category = 'chat', context_window = '8K' WHERE model_id = 'ernie-4.0-8k';
UPDATE api_models SET category = 'economy', context_window = '8K' WHERE model_id = 'ernie-3.5-8k';
UPDATE api_models SET category = 'economy', context_window = '8K' WHERE model_id = 'ernie-speed-8k';

-- Alibaba models
UPDATE api_models SET category = 'economy', context_window = '8K' WHERE model_id = 'qwen-turbo';
UPDATE api_models SET category = 'chat', context_window = '32K' WHERE model_id = 'qwen-plus';
UPDATE api_models SET category = 'chat', context_window = '32K' WHERE model_id = 'qwen-max';
UPDATE api_models SET category = 'long_context', context_window = '10M' WHERE model_id = 'qwen-long';

-- Add new models with vision capability
INSERT INTO api_models (provider_id, model_id, model_name, category, context_window, is_default, sort_order) VALUES
-- OpenAI vision models
(1, 'gpt-4-vision-preview', 'GPT-4 Vision', 'vision', '128K', false, 10),
(1, 'o1', 'o1', 'chat', '200K', false, 11),
(1, 'o1-mini', 'o1 Mini', 'chat', '128K', false, 12),
-- Anthropic vision models
(2, 'claude-3-5-sonnet', 'Claude 3.5 Sonnet (Latest)', 'vision', '200K', false, 4),
-- Google vision models
(3, 'gemini-2.0-flash', 'Gemini 2.0 Flash', 'vision', '1M', false, 4),
(3, 'gemini-1.5-pro-latest', 'Gemini 1.5 Pro (Latest)', 'vision', '2M', false, 5)
ON CONFLICT (provider_id, model_id) DO UPDATE SET 
    category = EXCLUDED.category,
    context_window = EXCLUDED.context_window;

-- Create index for category queries
CREATE INDEX IF NOT EXISTS idx_api_models_category ON api_models(category);
