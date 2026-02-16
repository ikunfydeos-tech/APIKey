import os
from datetime import timedelta
import secrets

class Settings:
    # Database - 从环境变量读取，无默认值
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/llm_api_manager")
    
    # Security - 生产环境必须设置环境变量
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        # 开发环境允许默认值，生产环境应报错
        if os.getenv("ENV", "development") == "production":
            raise ValueError("SECRET_KEY environment variable is required in production")
        SECRET_KEY = "dev-secret-key-change-in-production"
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Password hashing
    PWD_CONTEXT_SCHEME: str = "bcrypt"
    
    # API Key encryption - 生产环境必须设置
    _encryption_key_str = os.getenv("ENCRYPTION_KEY")
    if _encryption_key_str:
        API_KEY_ENCRYPTION_KEY: bytes = _encryption_key_str.encode()[:32].ljust(32, b'0')
    else:
        if os.getenv("ENV", "development") == "production":
            raise ValueError("ENCRYPTION_KEY environment variable is required in production")
        API_KEY_ENCRYPTION_KEY: bytes = b"dev-encryption-key-32-bytes!!"
    
    # CORS - 从环境变量读取允许的域名
    _cors_origins = os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS: list = _cors_origins.split(",") if _cors_origins != "*" else ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"
    
    # Remote Model Config
    MODEL_CONFIG_URL: str = os.getenv("MODEL_CONFIG_URL", "")
    MODEL_CONFIG_LOCAL_PATH: str = os.path.join(os.path.dirname(__file__), "model_config.json")

settings = Settings()