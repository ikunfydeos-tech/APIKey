from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(64))
    role = Column(String(20), default="user")  # "admin" or "user"
    
    # 会员等级：free(免费版), basic(基础版), pro(专业版)
    membership_tier = Column(String(20), default="free")
    membership_expire_at = Column(TIMESTAMP, nullable=True)  # 会员到期时间，null表示永久或免费版
    membership_started_at = Column(TIMESTAMP, nullable=True)  # 会员开始时间
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, default=True)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(TIMESTAMP, nullable=True)
    
    api_keys = relationship("UserApiKey", back_populates="user", cascade="all, delete-orphan")
    totp_config = relationship("TOTPConfig", back_populates="user", cascade="all, delete-orphan", uselist=False)

class ApiProvider(Base):
    __tablename__ = "api_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    base_url = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_custom = Column(Boolean, default=False)  # 是否为用户自定义服务商
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 创建者（仅自定义服务商）
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    api_keys = relationship("UserApiKey", back_populates="provider")
    models = relationship("ApiModel", back_populates="provider", cascade="all, delete-orphan")

class ApiModel(Base):
    __tablename__ = "api_models"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("api_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(String(100), nullable=False)
    model_name = Column(String(100))
    category = Column(String(50), default="chat")  # chat, code, long_context, economy, vision
    context_window = Column(String(20), nullable=True)  # e.g., "128K", "2M"
    is_default = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    provider = relationship("ApiProvider", back_populates="models")

class UserApiKey(Base):
    __tablename__ = "user_api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("api_providers.id", ondelete="SET NULL"), nullable=True)
    key_name = Column(String(100), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)
    api_key_preview = Column(String(20))
    model_id = Column(String(100), nullable=True)
    status = Column(String(20), default="active")
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(TIMESTAMP, nullable=True)
    
    user = relationship("User", back_populates="api_keys")
    provider = relationship("ApiProvider", back_populates="api_keys")

class LogEntry(Base):
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # 登录, 创建密钥, 删除密钥, 等
    resource_type = Column(String(50), nullable=True, index=True)  # API_KEY, USER, SYSTEM
    resource_id = Column(Integer, nullable=True)
    resource_name = Column(String(200), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), default="success")  # success, failed
    error_message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # JSON 格式的额外信息
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)

class TOTPConfig(Base):
    __tablename__ = "totp_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    secret = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="totp_config")

class TOTPLog(Base):
    __tablename__ = "totp_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)  # enable, disable, verify, failed
    ip_address = Column(String(45), nullable=True)
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
