from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str
    captcha_token: Optional[str] = None
    captcha_answer: Optional[str] = None

class CaptchaResponse(BaseModel):
    """验证码响应"""
    captcha_token: str
    captcha_image: str  # base64 encoded image

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str = "user"
    membership_tier: str = "free"
    membership_expire_at: Optional[datetime] = None
    membership_started_at: Optional[datetime] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# API Provider schemas
class ApiProviderBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    base_url: str
    description: Optional[str] = None
    icon: Optional[str] = None

class ApiProviderCreate(BaseModel):
    """用户创建自定义服务商"""
    display_name: str = Field(..., min_length=1, max_length=100)
    base_url: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None

class ApiProviderResponse(ApiProviderBase):
    id: int
    is_active: bool
    is_custom: bool = False
    created_by: Optional[int] = None
    sort_order: int
    
    class Config:
        from_attributes = True

# API Model schemas
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

class ApiModelWithProviderResponse(ApiModelResponse):
    provider_name: Optional[str] = None

# User API Key schemas
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

class UserApiKeyWithDecrypted(UserApiKeyResponse):
    api_key: str

# Generic response
class MessageResponse(BaseModel):
    message: str
    success: bool = True
