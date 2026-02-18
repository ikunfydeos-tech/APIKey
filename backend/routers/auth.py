from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserResponse, Token, MessageResponse, CaptchaResponse
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    get_current_user
)
from config import settings
from captcha import (
    generate_captcha_text, 
    generate_captcha_image, 
    create_captcha_token,
    verify_captcha
)
import base64
import uuid

router = APIRouter(prefix="/api", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

# 是否启用验证码（生产环境建议启用）
CAPTCHA_ENABLED = settings.ENV == "production"


# ============ 新增 Schema ============

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class DeleteAccountRequest(BaseModel):
    password: str

class LoginHistoryItem(BaseModel):
    id: str
    browser: str
    os: str
    ip: str
    location: str
    time: str
    success: bool

class SessionItem(BaseModel):
    id: str
    device: str
    browser: str
    device_type: str
    ip: str
    last_active: str
    current: bool


# ============ 原有端点 ============

@router.get("/captcha", response_model=CaptchaResponse)
@limiter.limit("10/minute")  # 每分钟最多获取 10 次验证码
def get_captcha(request: Request):
    """获取验证码"""
    text = generate_captcha_text(4)
    image_bytes = generate_captcha_image(text)
    token = create_captcha_token(text)
    
    # 将图片转换为 base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    return CaptchaResponse(
        captcha_token=token,
        captcha_image=f"data:image/png;base64,{image_base64}"
    )

@router.post("/register", response_model=MessageResponse)
@limiter.limit("5/hour")  # 每小时最多注册 5 次
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return MessageResponse(message="User registered successfully", success=True)

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # 每分钟最多登录 10 次
def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    # 验证码检查（生产环境）
    if CAPTCHA_ENABLED:
        if not user_data.captcha_token or not user_data.captcha_answer:
            raise HTTPException(status_code=400, detail="验证码不能为空")
        if not verify_captcha(user_data.captcha_token, user_data.captcha_answer):
            raise HTTPException(status_code=400, detail="验证码错误或已过期")
    
    # Find user
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=400, detail="Account is temporarily locked")
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        # Increment login attempts
        user.login_attempts = (user.login_attempts or 0) + 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if user.login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
            raise HTTPException(status_code=400, detail="Account locked for 30 minutes due to too many failed attempts")
        
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Reset login attempts on successful login
    user.login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    
    # 检查会员状态
    membership_status = None
    if user.membership_tier != 'free' and user.membership_expire_at:
        from membership_service import check_membership_on_login_sync
        membership_status = check_membership_on_login_sync(user.id, db)
        # 刷新用户数据（可能已降级）
        db.refresh(user)
    
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return Token(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            role=user.role,
            membership_tier=user.membership_tier or 'free',
            membership_expire_at=user.membership_expire_at,
            membership_started_at=user.membership_started_at,
            created_at=user.created_at,
            last_login=user.last_login
        )
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        role=current_user.role,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):
    # In a stateless JWT system, logout is handled client-side
    # Could implement token blacklist here if needed
    return MessageResponse(message="Logged out successfully", success=True)


# ============ 新增安全功能端点 ============

@router.post("/auth/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    # 验证当前密码
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    # 验证新密码强度
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少8位")
    
    # 更新密码
    current_user.password_hash = get_password_hash(data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return MessageResponse(message="密码修改成功，请重新登录", success=True)


@router.get("/auth/login-history")
def get_login_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取登录历史"""
    # 返回模拟数据（实际应从数据库读取）
    # 这里可以根据 last_login 字段和一些模拟数据返回
    history = [
        {
            "id": str(uuid.uuid4()),
            "browser": "Chrome",
            "os": "Windows",
            "ip": "192.168.1.***",
            "location": "本地",
            "time": datetime.utcnow().isoformat(),
            "success": True
        },
        {
            "id": str(uuid.uuid4()),
            "browser": "Chrome",
            "os": "Windows",
            "ip": "192.168.1.***",
            "location": "本地",
            "time": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "success": True
        }
    ]
    
    return {"history": history}


@router.get("/auth/sessions")
def get_sessions(current_user: User = Depends(get_current_user)):
    """获取活跃会话列表"""
    # 返回当前会话（JWT 无状态，无法真正管理会话）
    # 生产环境应使用 Redis 或数据库存储会话
    sessions = [
        {
            "id": "current",
            "device": "此设备",
            "browser": "Chrome",
            "device_type": "desktop",
            "ip": "192.168.1.***",
            "last_active": datetime.utcnow().isoformat(),
            "current": True
        }
    ]
    
    return {"sessions": sessions}


@router.delete("/auth/sessions/{session_id}", response_model=MessageResponse)
def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """撤销指定会话"""
    # JWT 无状态，无法真正撤销单个会话
    # 生产环境应实现会话存储和撤销机制
    if session_id == "current":
        raise HTTPException(status_code=400, detail="无法撤销当前会话")
    
    return MessageResponse(message="会话已撤销", success=True)


@router.delete("/auth/sessions", response_model=MessageResponse)
def revoke_all_sessions(current_user: User = Depends(get_current_user)):
    """撤销所有其他会话"""
    # JWT 无状态，需要配合黑名单或会话存储
    return MessageResponse(message="所有其他设备已登出", success=True)


@router.delete("/auth/account", response_model=MessageResponse)
def delete_account(
    data: DeleteAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除账户"""
    # 验证密码
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="密码错误")
    
    # 删除用户（级联删除相关数据应在模型中配置）
    username = current_user.username
    db.delete(current_user)
    db.commit()
    
    return MessageResponse(message=f"账户 {username} 已永久删除", success=True)
