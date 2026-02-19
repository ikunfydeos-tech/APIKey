# 重构版认证路由 - 强制TOTP注册
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from models_v2 import User, TOTPConfig, LoginHistory, LogEntry
from schemas import UserCreate, UserLogin, UserResponse, Token, MessageResponse
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    get_current_user
)
from totp_utils import generate_totp_secret, verify_totp_code
from config import settings
import base64

router = APIRouter(prefix="/api", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

# ============ 请求模型 ============

class RegisterStep1Request(BaseModel):
    """注册第一步：基本信息"""
    username: str
    email: str
    password: str

class RegisterStep2Request(BaseModel):
    """注册第二步：TOTP验证"""
    temp_token: str
    totp_code: str

class LoginWithTOTPRequest(BaseModel):
    """登录请求（含TOTP）"""
    username: str
    password: str
    totp_code: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class DeleteAccountRequest(BaseModel):
    password: str


# ============ 临时token存储（生产环境应使用Redis）===========
# 内存存储，重启后丢失
temp_registration_store = {}


def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """获取User Agent"""
    return request.headers.get("User-Agent", "")


def log_user_action(db: Session, user_id: int, username: str, action: str, 
                   ip_address: str, user_agent: str, status: str = "success",
                   resource_type: str = None, resource_id: int = None, 
                   resource_name: str = None, details: dict = None):
    """记录用户操作日志"""
    log = LogEntry(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        details=str(details) if details else None
    )
    db.add(log)
    db.commit()


def record_login_history(db: Session, user_id: int, ip_address: str, user_agent: str,
                        login_type: str = "password", status: str = "success", 
                        fail_reason: str = None):
    """记录登录历史"""
    history = LoginHistory(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        login_type=login_type,
        status=status,
        fail_reason=fail_reason
    )
    db.add(history)
    db.commit()


# ============ 注册流程（强制TOTP）===========

@router.post("/register/step1")
@limiter.limit("5/hour")
def register_step1(request: Request, user_data: RegisterStep1Request, db: Session = Depends(get_db)):
    """
    注册第一步：验证基本信息，生成TOTP密钥
    返回临时token和TOTP二维码
    """
    # 检查用户名
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已被使用")
    
    # 检查邮箱
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 密码强度验证
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少8位")
    
    # 生成TOTP密钥
    secret = generate_totp_secret()
    
    # 生成临时token（有效期10分钟）
    import secrets
    temp_token = secrets.token_urlsafe(32)
    
    # 存储临时注册信息
    temp_registration_store[temp_token] = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "totp_secret": secret,
        "created_at": datetime.utcnow(),
        "ip": get_client_ip(request)
    }
    
    # 生成二维码
    import qrcode
    import io
    
    # TOTP URI
    totp_uri = f"otpauth://totp/LLM-API-Manager:{user_data.username}?secret={secret}&issuer=LLM-API-Manager"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "temp_token": temp_token,
        "totp_secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "message": "请使用Authenticator应用扫描二维码，然后输入6位验证码完成注册",
        "success": True
    }


@router.post("/register/step2")
@limiter.limit("10/minute")
def register_step2(request: Request, data: RegisterStep2Request, db: Session = Depends(get_db)):
    """
    注册第二步：验证TOTP，完成注册
    """
    # 检查临时token
    reg_data = temp_registration_store.get(data.temp_token)
    if not reg_data:
        raise HTTPException(status_code=400, detail="注册会话已过期，请重新开始注册")
    
    # 检查是否过期（10分钟）
    if datetime.utcnow() - reg_data["created_at"] > timedelta(minutes=10):
        del temp_registration_store[data.temp_token]
        raise HTTPException(status_code=400, detail="注册会话已过期，请重新开始注册")
    
    # 验证TOTP
    if not verify_totp_code(reg_data["totp_secret"], data.totp_code):
        raise HTTPException(status_code=400, detail="TOTP验证码错误")
    
    # 创建用户
    new_user = User(
        username=reg_data["username"],
        email=reg_data["email"],
        password_hash=reg_data["password_hash"],
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 创建TOTP配置
    totp_config = TOTPConfig(
        user_id=new_user.id,
        secret=reg_data["totp_secret"],
        is_enabled=True
    )
    db.add(totp_config)
    db.commit()
    
    # 记录日志
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    log_user_action(db, new_user.id, new_user.username, "用户注册", ip, ua)
    
    # 清理临时数据
    del temp_registration_store[data.temp_token]
    
    # 生成登录token
    access_token = create_access_token(data={"sub": new_user.username})
    
    return Token(
        access_token=access_token,
        user=UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login=new_user.last_login
        )
    )


# ============ 登录（强制TOTP）===========

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, user_data: LoginWithTOTPRequest, db: Session = Depends(get_db)):
    """
    登录（需要TOTP）
    """
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    # 查找用户
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查账户锁定
    if user.locked_until and user.locked_until > datetime.utcnow():
        record_login_history(db, user.id, ip, ua, "password", "failed", "账户已锁定")
        raise HTTPException(status_code=400, detail="账户已锁定，请稍后再试")
    
    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        user.login_attempts = (user.login_attempts or 0) + 1
        
        # 5次失败后锁定30分钟
        if user.login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
            record_login_history(db, user.id, ip, ua, "password", "failed", "多次失败，账户已锁定")
            raise HTTPException(status_code=400, detail="多次登录失败，账户已锁定30分钟")
        
        db.commit()
        record_login_history(db, user.id, ip, ua, "password", "failed", "密码错误")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证TOTP
    totp_config = db.query(TOTPConfig).filter(TOTPConfig.user_id == user.id).first()
    if not totp_config or not totp_config.is_enabled:
        record_login_history(db, user.id, ip, ua, "totp", "failed", "TOTP未启用")
        raise HTTPException(status_code=400, detail="账户安全设置异常，请联系管理员")
    
    if not verify_totp_code(totp_config.secret, user_data.totp_code):
        user.login_attempts = (user.login_attempts or 0) + 1
        db.commit()
        record_login_history(db, user.id, ip, ua, "totp", "failed", "TOTP验证码错误")
        raise HTTPException(status_code=400, detail="TOTP验证码错误")
    
    # 登录成功
    user.login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 记录登录历史
    record_login_history(db, user.id, ip, ua, "totp", "success")
    log_user_action(db, user.id, user.username, "用户登录", ip, ua)
    
    # 生成token
    access_token = create_access_token(data={"sub": user.username})
    
    return Token(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    )


# ============ 用户信息 ============

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    log_user_action(db, current_user.id, current_user.username, "用户登出", ip, ua)
    return MessageResponse(message="登出成功", success=True)


# ============ 安全功能 ============

@router.post("/auth/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    # 验证当前密码
    if not verify_password(data.current_password, current_user.password_hash):
        log_user_action(db, current_user.id, current_user.username, "修改密码", ip, ua, "failed", details={"error": "当前密码错误"})
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    # 验证新密码强度
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少8位")
    
    # 更新密码
    current_user.password_hash = get_password_hash(data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    log_user_action(db, current_user.id, current_user.username, "修改密码", ip, ua, details={"message": "密码修改成功"})
    
    return MessageResponse(message="密码修改成功，请重新登录", success=True)


@router.delete("/auth/account", response_model=MessageResponse)
def delete_account(
    request: Request,
    data: DeleteAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除账户"""
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    # 验证密码
    if not verify_password(data.password, current_user.password_hash):
        log_user_action(db, current_user.id, current_user.username, "删除账户", ip, ua, "failed", details={"error": "密码错误"})
        raise HTTPException(status_code=400, detail="密码错误")
    
    username = current_user.username
    user_id = current_user.id
    
    # 删除用户（级联删除相关数据）
    db.delete(current_user)
    db.commit()
    
    # 记录日志（用户已删除，使用临时记录）
    log = LogEntry(
        user_id=0,
        username=username,
        action="删除账户",
        ip_address=ip,
        user_agent=ua,
        status="success",
        details=f"用户 {username} (ID: {user_id}) 已删除账户"
    )
    db.add(log)
    db.commit()
    
    return MessageResponse(message=f"账户 {username} 已永久删除", success=True)


# ============ 登录历史和日志查看 ============

@router.get("/auth/login-history")
def get_login_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取登录历史"""
    from sqlalchemy import desc
    
    query = db.query(LoginHistory).filter(LoginHistory.user_id == current_user.id)
    total = query.count()
    
    history = query.order_by(desc(LoginHistory.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "history": [
            {
                "id": h.id,
                "ip_address": h.ip_address,
                "location": h.location,
                "login_type": h.login_type,
                "status": h.status,
                "fail_reason": h.fail_reason,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in history
        ]
    }


@router.get("/auth/logs")
def get_user_logs(
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户操作日志"""
    from sqlalchemy import desc
    
    query = db.query(LogEntry).filter(LogEntry.user_id == current_user.id)
    
    if action:
        query = query.filter(LogEntry.action.ilike(f"%{action}%"))
    
    total = query.count()
    
    logs = query.order_by(desc(LogEntry.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address,
                "status": log.status,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    }


@router.get("/auth/log-actions")
def get_log_actions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的操作类型列表"""
    from sqlalchemy import distinct
    
    actions = db.query(distinct(LogEntry.action))\
        .filter(LogEntry.user_id == current_user.id)\
        .all()
    
    return [a[0] for a in actions if a[0]]
