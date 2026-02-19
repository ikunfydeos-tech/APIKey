# TOTP工具函数
import base64
import secrets
from typing import Tuple

def generate_totp_secret() -> str:
    """生成新的TOTP密钥"""
    # 生成20字节的随机密钥（标准的TOTP密钥长度，避免填充问题）
    # 20字节 = 160位，Base32编码后正好32字符，无需填充
    random_bytes = secrets.token_bytes(20)
    # 使用base32编码（TOTP标准）
    return base64.b32encode(random_bytes).decode('utf-8').rstrip('=')


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """
    验证TOTP验证码
    
    Args:
        secret: TOTP密钥（base32编码，可以有或没有填充符）
        code: 用户输入的6位验证码
        window: 时间窗口容错（前后各window个时间窗口）
    
    Returns:
        bool: 验证是否通过
    """
    try:
        import pyotp
        # 确保密钥格式正确（Base32 需要填充符）
        # pyotp 要求密钥长度必须是8的倍数，不足则用 '=' 填充
        padded_secret = secret
        if len(secret) % 8 != 0:
            padded_secret = secret + '=' * (8 - len(secret) % 8)
        
        totp = pyotp.TOTP(padded_secret)
        return totp.verify(code, valid_window=window)
    except Exception as e:
        print(f"TOTP验证异常: {e}")
        return False


def generate_qr_code_base64(username: str, secret: str) -> str:
    """
    生成TOTP二维码的base64编码
    
    Args:
        username: 用户名
        secret: TOTP密钥
    
    Returns:
        str: base64编码的PNG图片
    """
    try:
        import qrcode
        import io
        
        # TOTP URI
        totp_uri = f"otpauth://totp/LLM-API-Manager:{username}?secret={secret}&issuer=LLM-API-Manager"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        print(f"生成二维码失败: {e}")
        return ""


def get_totp_uri(username: str, secret: str) -> str:
    """获取TOTP URI（用于手动添加到验证器）"""
    return f"otpauth://totp/LLM-API-Manager:{username}?secret={secret}&issuer=LLM-API-Manager"


def generate_backup_codes(count: int = 8) -> list:
    """
    生成备用验证码
    
    Args:
        count: 生成数量
    
    Returns:
        list: 备用验证码列表
    """
    codes = []
    for _ in range(count):
        # 生成8位数字
        code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
        codes.append(code)
    return codes
