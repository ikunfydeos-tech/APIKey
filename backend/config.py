import os
import logging
from datetime import timedelta
import secrets

logger = logging.getLogger(__name__)

class Settings:
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"
    
    # Database - 生产环境必须设置环境变量
    _database_url = os.getenv("DATABASE_URL")
    if not _database_url:
        if ENV == "production":
            raise ValueError("DATABASE_URL environment variable is required in production")
        # 开发环境提示用户配置数据库
        _database_url = "postgresql://postgres:your_password@localhost:5432/llm_api_manager"
        logger.warning("⚠️  使用示例数据库连接，请配置 .env 文件中的 DATABASE_URL")
    DATABASE_URL: str = _database_url
    
    # Security - 生产环境必须设置环境变量
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if ENV == "production":
            raise ValueError("SECRET_KEY environment variable is required in production")
        # 开发环境生成随机密钥并警告
        SECRET_KEY = secrets.token_urlsafe(32)
        logger.warning("⚠️  使用自动生成的 SECRET_KEY（仅限开发环境）")
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Password hashing
    PWD_CONTEXT_SCHEME: str = "bcrypt"
    
    # API Key encryption - 生产环境必须设置
    _encryption_key_str = os.getenv("ENCRYPTION_KEY")
    if _encryption_key_str:
        API_KEY_ENCRYPTION_KEY: bytes = _encryption_key_str.encode()[:32].ljust(32, b'0')
    else:
        if ENV == "production":
            raise ValueError("ENCRYPTION_KEY environment variable is required in production")
        # 开发环境生成随机密钥并警告
        API_KEY_ENCRYPTION_KEY: bytes = secrets.token_bytes(32)
        logger.warning("⚠️  使用自动生成的 ENCRYPTION_KEY（仅限开发环境，已有加密数据将无法解密）")
    
    # Encryption salt - 用于密钥加密的盐值
    _encryption_salt = os.getenv("ENCRYPTION_SALT")
    if _encryption_salt:
        ENCRYPTION_SALT: bytes = _encryption_salt.encode()[:16].ljust(16, b'0')
    else:
        if ENV == "production":
            raise ValueError("ENCRYPTION_SALT environment variable is required in production")
        ENCRYPTION_SALT: bytes = b"dev-salt-16-byte"
        logger.warning("⚠️  使用默认 ENCRYPTION_SALT（仅限开发环境）")
    
    # CORS - 从环境变量读取允许的域名
    _cors_origins = os.getenv("CORS_ORIGINS")
    if _cors_origins:
        CORS_ORIGINS: list = _cors_origins.split(",")
    else:
        if ENV == "production":
            raise ValueError("CORS_ORIGINS environment variable is required in production")
        CORS_ORIGINS: list = ["*"]
        logger.warning("⚠️  CORS 允许所有来源（仅限开发环境）")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Remote Model Config
    MODEL_CONFIG_URL: str = os.getenv("MODEL_CONFIG_URL", "")
    MODEL_CONFIG_LOCAL_PATH: str = os.path.join(os.path.dirname(__file__), "model_config.json")
    
    def validate_production(self):
        """启动时验证生产环境配置"""
        if self.ENV == "production":
            issues = []
            
            if len(self.SECRET_KEY) < 32:
                issues.append("SECRET_KEY 长度不足 32 字符")
            
            if len(self.API_KEY_ENCRYPTION_KEY) < 32:
                issues.append("ENCRYPTION_KEY 长度不足 32 字节")
            
            if "*" in self.CORS_ORIGINS:
                issues.append("CORS_ORIGINS 包含通配符 '*'")
            
            if issues:
                logger.error("❌ 生产环境安全配置问题:")
                for issue in issues:
                    logger.error(f"   - {issue}")
                raise ValueError(f"Production security issues: {', '.join(issues)}")
            
            logger.info("✅ 生产环境安全配置验证通过")
        
        return True

settings = Settings()

# 启动时验证
settings.validate_production()