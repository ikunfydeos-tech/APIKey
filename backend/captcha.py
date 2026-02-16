"""
验证码生成和验证模块
"""
import random
import string
import io
import hashlib
import time
from PIL import Image, ImageDraw, ImageFont
from jose import jwt
from config import settings

# 验证码有效期（秒）
CAPTCHA_EXPIRE_SECONDS = 300  # 5分钟

def generate_captcha_text(length: int = 4) -> str:
    """生成随机验证码文本"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_captcha_image(text: str) -> bytes:
    """生成验证码图片"""
    # 图片尺寸
    width, height = 120, 40
    
    # 创建图片
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 使用默认字体（如果系统有其他字体可以指定）
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()
    
    # 绘制干扰线
    for _ in range(3):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200), width=1)
    
    # 绘制干扰点
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    # 绘制验证码文字
    text_width = len(text) * 25
    x = (width - text_width) // 2
    for i, char in enumerate(text):
        # 随机颜色
        color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        # 随机偏移
        y = random.randint(5, 15)
        draw.text((x + i * 25, y), char, font=font, fill=color)
    
    # 转换为字节
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

def create_captcha_token(text: str) -> str:
    """创建验证码 token（包含答案和过期时间）"""
    payload = {
        "answer": text.lower(),
        "exp": int(time.time()) + CAPTCHA_EXPIRE_SECONDS
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_captcha(token: str, user_input: str) -> bool:
    """验证验证码"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("answer") == user_input.lower()
    except:
        return False
