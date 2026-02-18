import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from auth import get_current_user
from models import User, TOTPConfig
from database import get_db
from totp_utils import (
    generate_totp_secret, generate_qr_code_base64, 
    enable_totp_for_user, disable_totp_for_user, 
    is_totp_enabled, verify_totp_token
)

router = APIRouter(prefix="/api/totp", tags=["totp"])

@router.get("/secret")
def get_totp_secret(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的 TOTP 秘钥"""
    # 检查是否已有配置
    config = db.query(TOTPConfig).filter(TOTPConfig.user_id == current_user.id).first()
    
    if not config:
        # 生成新的秘钥
        secret = generate_totp_secret()
    else:
        secret = config.secret
    
    qr_code = generate_qr_code_base64(current_user.username, secret)
    
    return {
        "secret": secret,
        "qr_code": qr_code,
        "is_enabled": config.is_enabled if config else False,
        "success": True
    }

@router.post("/enable")
def enable_totp(
    request: Request,
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启用 TOTP"""
    # 验证令牌
    is_valid, message = verify_totp_token(db, current_user.id, token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # 生成秘钥并启用
    secret = generate_totp_secret()
    if enable_totp_for_user(db, current_user.id, secret):
        return {
            "message": "TOTP 已启用",
            "secret": secret,
            "success": True
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启用 TOTP 失败"
        )

@router.post("/disable")
def disable_totp(
    request: Request,
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """禁用 TOTP"""
    # 验证令牌
    is_valid, message = verify_totp_token(db, current_user.id, token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    if disable_totp_for_user(db, current_user.id):
        return {
            "message": "TOTP 已禁用",
            "success": True
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="禁用 TOTP 失败"
        )

@router.post("/verify")
def verify_totp(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """验证 TOTP 令牌"""
    is_valid, message = verify_totp_token(db, current_user.id, token)
    return {
        "is_valid": is_valid,
        "message": message,
        "success": True
    }

@router.get("/status")
def get_totp_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取 TOTP 状态"""
    is_enabled = is_totp_enabled(db, current_user.id)
    return {
        "is_enabled": is_enabled,
        "success": True
    }