import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import TOTPConfig, TOTPLog

def generate_totp_secret():
    """生成 TOTP 秘钥"""
    return pyotp.random_base32()

def get_totp_uri(username: str, secret: str):
    """生成 TOTP URI"""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name="API密钥管理系统"
    )

def generate_qr_code_base64(username: str, secret: str):
    """生成二维码并返回 base64 编码"""
    uri = get_totp_uri(username, secret)
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def verify_totp_code(secret: str, token: str):
    """验证 TOTP 令牌"""
    totp = pyotp.TOTP(secret)
    # 允许 1 个时间窗口的偏差（30秒）
    return totp.verify(token, valid_window=1)

def log_totp_action(
    db: Session,
    user_id: int,
    username: str,
    action: str,
    ip_address: str = None,
    status: str = "success",
    error_message: str = None,
    details: dict = None
):
    """记录 TOTP 操作日志"""
    try:
        log_entry = TOTPLog(
            user_id=user_id,
            username=username,
            action=action,
            ip_address=ip_address,
            status=status,
            error_message=error_message,
            details=str(details) if details else None
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Failed to log TOTP action: {e}")

def enable_totp_for_user(db: Session, user_id: int, secret: str):
    """为用户启用 TOTP"""
    try:
        # 检查是否已有配置
        existing = db.query(TOTPConfig).filter(TOTPConfig.user_id == user_id).first()
        
        if existing:
            existing.secret = secret
            existing.is_enabled = True
            existing.updated_at = datetime.utcnow()
        else:
            config = TOTPConfig(
                user_id=user_id,
                secret=secret,
                is_enabled=True
            )
            db.add(config)
        
        db.commit()
        log_totp_action(db, user_id, None, "enable", status="success")
        return True
    except Exception as e:
        log_totp_action(db, user_id, None, "enable", status="failed", error_message=str(e))
        return False

def disable_totp_for_user(db: Session, user_id: int):
    """为用户禁用 TOTP"""
    try:
        config = db.query(TOTPConfig).filter(TOTPConfig.user_id == user_id).first()
        if config:
            config.is_enabled = False
            config.updated_at = datetime.utcnow()
            db.commit()
            log_totp_action(db, user_id, None, "disable", status="success")
            return True
        return False
    except Exception as e:
        log_totp_action(db, user_id, None, "disable", status="failed", error_message=str(e))
        return False

def is_totp_enabled(db: Session, user_id: int):
    """检查用户是否启用了 TOTP"""
    config = db.query(TOTPConfig).filter(TOTPConfig.user_id == user_id).first()
    return config and config.is_enabled

def verify_totp_token(db: Session, user_id: int, token: str):
    """验证 TOTP 令牌"""
    try:
        config = db.query(TOTPConfig).filter(TOTPConfig.user_id == user_id).first()
        if not config or not config.is_enabled:
            return False, "TOTP 未启用"
        
        # 获取当前用户名
        from models import User
        user = db.query(User).filter(User.id == user_id).first()
        username = user.username if user else None
        
        if verify_totp_code(config.secret, token):
            log_totp_action(db, user_id, username, "verify", status="success")
            return True, "验证成功"
        else:
            log_totp_action(db, user_id, username, "failed", status="failed", error_message="令牌无效")
            return False, "令牌无效"
    except Exception as e:
        log_totp_action(db, user_id, None, "failed", status="failed", error_message=str(e))
        return False, str(e)