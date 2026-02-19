# 重构版模型定义 - 移除管理员，用户自主管理
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(64))
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, default=True)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(TIMESTAMP, nullable=True)
    
    api_keys = relationship("UserApiKey", back_populates="user", cascade="all, delete-orphan")
    totp_config = relationship("TOTPConfig", back_populates="user", cascade="all, delete-orphan", uselist=False)
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("LogEntry", back_populates="user", cascade="all, delete-orphan")
    token_usage = relationship("TokenUsage", back_populates="user", cascade="all, delete-orphan")

class ApiProvider(Base):
    __tablename__ = "api_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    base_url = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    api_keys = relationship("UserApiKey", back_populates="provider")
    models = relationship("ApiModel", back_populates="provider", cascade="all, delete-orphan")
    token_usage = relationship("TokenUsage", back_populates="provider")

class ApiModel(Base):
    __tablename__ = "api_models"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("api_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(String(100), nullable=False)
    model_name = Column(String(100))
    category = Column(String(50), default="chat")
    context_window = Column(String(20), nullable=True)
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
    expires_at = Column(TIMESTAMP, nullable=True)
    
    user = relationship("User", back_populates="api_keys")
    provider = relationship("ApiProvider", back_populates="api_keys")
    token_usage = relationship("TokenUsage", back_populates="key")
    balances = relationship("KeyBalance", back_populates="key", cascade="all, delete-orphan")
    renewals = relationship("RenewalRecord", back_populates="key", cascade="all, delete-orphan")

class TOTPConfig(Base):
    __tablename__ = "totp_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    secret = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="totp_config")

class LogEntry(Base):
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    resource_name = Column(String(200), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="logs")

class LoginHistory(Base):
    __tablename__ = "login_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    login_type = Column(String(20), default="password")
    status = Column(String(20), default="success")
    fail_reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="login_history")

class TokenUsage(Base):
    __tablename__ = "token_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_id = Column(Integer, ForeignKey("user_api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("api_providers.id"), nullable=True)
    model_id = Column(String(100), nullable=True)
    request_tokens = Column(Integer, default=0)
    response_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Numeric(10, 6), nullable=True)
    request_id = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="token_usage")
    key = relationship("UserApiKey", back_populates="token_usage")
    provider = relationship("ApiProvider", back_populates="token_usage")

class KeyBalance(Base):
    __tablename__ = "key_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(Integer, ForeignKey("user_api_keys.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(Integer, ForeignKey("api_providers.id"), nullable=True)
    balance = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(10), default="USD")
    total_usage = Column(Numeric(10, 2), default=0)
    total_requests = Column(Integer, default=0)
    last_checked_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    key = relationship("UserApiKey", back_populates="balances")

class RenewalRecord(Base):
    __tablename__ = "renewal_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_id = Column(Integer, ForeignKey("user_api_keys.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(Integer, ForeignKey("api_providers.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    duration_days = Column(Integer, nullable=True)
    expires_at = Column(TIMESTAMP, nullable=True)
    status = Column(String(20), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    key = relationship("UserApiKey", back_populates="renewals")
