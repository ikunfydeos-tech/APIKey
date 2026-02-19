"""
TOTP认证路由
注意：注册时强制启用TOTP，此路由主要用于：
1. 查看当前TOTP状态
2. 验证TOTP码（用于敏感操作验证）
3. 重新生成TOTP（需要验证当前TOTP）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from auth import get_current_user
from models_v2 import User, TOTPConfig
from database import get_db
from totp_utils import generate_totp_secret, verify_totp_code, generate_qr_code_base64
from datetime import datetime
import base64

router = APIRouter(prefix="/api/totp", tags=["totp"])


@router.get("/status")
def get_totp_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取TOTP状态"""
    config = db.query(TOTPConfig).filter(TOTPConfig.user_id == current_user.id).first()
    
    return {
        "is_enabled": config.is_enabled if config else False,
        "created_at": config.created_at.isoformat() if config and config.created_at else None,
        "success": True
    }


@router.post("/verify")
def verify_totp(
    request: Request,
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """验证TOTP验证码（用于敏感操作前的二次验证）"""
    config = db.query(TOTPConfig).filter(TOTPConfig.user_id == current_user.id).first()
    
    if not config or not config.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP未启用"
        )
    
    is_valid = verify_totp_code(config.secret, code)
    
    return {
        "is_valid": is_valid,
        "message": "验证通过" if is_valid else "验证码错误",
        "success": is_valid
    }


@router.get("/regenerate")
def regenerate_totp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重新生成TOTP密钥（需要先验证当前TOTP）
    返回新的密钥和二维码，需要用户确认后才会生效
    """
    config = db.query(TOTPConfig).filter(TOTPConfig.user_id == current_user.id).first()
    
    if not config or not config.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先启用TOTP"
        )
    
    # 生成新的临时密钥（不会立即生效）
    new_secret = generate_totp_secret()
    qr_code = generate_qr_code_base64(current_user.username, new_secret)
    
    # 存储临时密钥（实际应用中应该用Redis，这里简化处理）
    # 这里返回新密钥，用户需要在确认接口中验证新密钥
    
    return {
        "new_secret": new_secret,
        "qr_code": f"data:image/png;base64,{qr_code}",
        "message": "请扫描新二维码，然后使用新验证码确认更新",
        "success": True
    }


@router.post("/confirm-regenerate")
def confirm_regenerate_totp(
    request: Request,
    old_code: str,
    new_code: str,
    new_secret: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认更新TOTP密钥"""
    config = db.query(TOTPConfig).filter(TOTPConfig.user_id == current_user.id).first()
    
    if not config or not config.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP未启用"
        )
    
    # 验证旧验证码
    if not verify_totp_code(config.secret, old_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前TOTP验证码错误"
        )
    
    # 验证新验证码
    if not verify_totp_code(new_secret, new_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新TOTP验证码错误"
        )
    
    # 更新密钥
    config.secret = new_secret
    config.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "TOTP密钥已更新",
        "success": True
    }


@router.get("/backup-codes")
def generate_backup_codes_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成备用验证码"""
    from totp_utils import generate_backup_codes
    
    config = db.query(TOTPConfig).filter(TOTPConfig.user_id == current_user.id).first()
    
    if not config or not config.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP未启用"
        )
    
    codes = generate_backup_codes(8)
    
    return {
        "backup_codes": codes,
        "message": "请妥善保管备用验证码，每个验证码只能使用一次",
        "success": True
    }
