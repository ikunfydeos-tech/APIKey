# 重构版Schemas - 移除管理员相关字段
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# ============ 用户相关 ============

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str
    totp_code: str = Field(..., min_length=6, max_length=6)

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============ 注册流程 ============

class RegisterStep1Request(BaseModel):
    """注册第一步：基本信息"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

class RegisterStep1Response(BaseModel):
    """注册第一步响应"""
    temp_token: str
    totp_secret: str
    qr_code: str  # base64编码的二维码
    message: str
    success: bool

class RegisterStep2Request(BaseModel):
    """注册第二步：TOTP验证"""
    temp_token: str
    totp_code: str = Field(..., min_length=6, max_length=6)


# ============ 服务商和模型 ============

class ApiProviderResponse(BaseModel):
    id: int
    name: str
    display_name: Optional[str] = None
    base_url: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool
    sort_order: int
    
    class Config:
        from_attributes = True

class ApiModelResponse(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}
    
    id: int
    provider_id: int
    model_id: str
    model_name: Optional[str]
    category: Optional[str] = "chat"
    context_window: Optional[str] = None
    is_default: bool
    sort_order: int


# ============ API密钥 ============

class UserApiKeyCreate(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    provider_id: int
    key_name: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=1)
    model_id: Optional[str] = None
    notes: Optional[str] = None

class UserApiKeyUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    key_name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|expired)$")
    notes: Optional[str] = None

class UserApiKeyResponse(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}
    
    id: int
    provider_id: Optional[int]
    provider_name: Optional[str] = None
    key_name: str
    api_key_preview: Optional[str]
    model_id: Optional[str] = None
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime] = None

class UserApiKeyWithDecrypted(UserApiKeyResponse):
    api_key: str


# ============ 日志和历史 ============

class LoginHistoryItem(BaseModel):
    id: int
    ip_address: str
    location: Optional[str] = None
    login_type: str
    status: str
    fail_reason: Optional[str] = None
    created_at: str

class LoginHistoryResponse(BaseModel):
    total: int
    page: int
    page_size: int
    history: List[LoginHistoryItem]

class LogEntryItem(BaseModel):
    id: int
    action: str
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    ip_address: Optional[str] = None
    status: str
    details: Optional[str] = None
    created_at: str

class UserLogsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    logs: List[LogEntryItem]


# ============ Token使用和余额 ============

class TokenUsageItem(BaseModel):
    id: int
    model_id: Optional[str]
    request_tokens: int
    response_tokens: int
    total_tokens: int
    cost: Optional[float] = None
    created_at: str

class TokenUsageResponse(BaseModel):
    key_id: int
    key_name: str
    days: int
    total_records: int
    usage: List[TokenUsageItem]

class KeyBalanceResponse(BaseModel):
    key_id: int
    key_name: str
    provider_id: Optional[int]
    balance: Optional[float] = None
    currency: str
    total_usage: float
    total_requests: int
    total_tokens: int
    last_checked_at: Optional[str] = None

class KeyStatsModel(BaseModel):
    model_id: str
    request_count: int
    token_count: int
    total_cost: float

class DailyStats(BaseModel):
    date: str
    requests: int
    tokens: int
    cost: float

class KeyStatsResponse(BaseModel):
    key_id: int
    key_name: str
    overall: dict
    by_model: List[KeyStatsModel]
    last_7_days: List[DailyStats]


# ============ 续费 ============

class RenewalRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    duration_days: Optional[int] = None
    notes: Optional[str] = None

class RenewalRecordItem(BaseModel):
    id: int
    amount: float
    currency: str
    duration_days: Optional[int]
    expires_at: Optional[str]
    status: str
    notes: Optional[str]
    created_at: str

class RenewalResponse(BaseModel):
    success: bool
    message: str
    renewal_id: int
    key_id: int
    new_expires_at: Optional[str]

class RenewalHistoryResponse(BaseModel):
    key_id: int
    key_name: str
    renewals: List[RenewalRecordItem]


# ============ 通用响应 ============

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str
