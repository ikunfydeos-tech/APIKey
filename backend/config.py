import os
from datetime import timedelta

class Settings:
    # Database
    DATABASE_URL: str = "postgresql://postgres:123456@localhost:5432/llm_api_manager"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Password hashing
    PWD_CONTEXT_SCHEME: str = "bcrypt"
    
    # API Key encryption
    API_KEY_ENCRYPTION_KEY: bytes = b"your-32-byte-encryption-key-here!"  # 32 bytes for AES-256
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Remote Model Config
    # You can host this file on GitHub Raw, CDN, or any static file server
    # Example: https://raw.githubusercontent.com/your-repo/api-manager/main/model_config.json
    MODEL_CONFIG_URL: str = os.getenv("MODEL_CONFIG_URL", "")
    MODEL_CONFIG_LOCAL_PATH: str = os.path.join(os.path.dirname(__file__), "model_config.json")

settings = Settings()
