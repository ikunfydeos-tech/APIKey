from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
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

router = APIRouter(prefix="/api", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

# 是否启用验证码（生产环境建议启用）
CAPTCHA_ENABLED = settings.ENV == "production"

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
            created_at=user.created_at
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
        created_at=current_user.created_at
    )

@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):
    # In a stateless JWT system, logout is handled client-side
    # Could implement token blacklist here if needed
    return MessageResponse(message="Logged out successfully", success=True)
