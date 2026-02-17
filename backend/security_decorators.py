from functools import wraps
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from auth import get_current_user
from models import User

# 高危操作列表
HIGH_RISK_OPERATIONS = [
    '删除用户',
    '删除密钥',
    '禁用用户',
    '修改用户角色',
    '删除服务商',
    '删除模型',
    '清空配置'
]

def require_confirm(action: str):
    """
    高危操作二次确认装饰器
    检查用户是否已经确认过该操作
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中获取用户
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法获取请求信息"
                )
            
            # 获取当前用户
            current_user = await get_current_user(request)
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未授权"
                )
            
            # 检查是否为高危操作
            if action in HIGH_RISK_OPERATIONS:
                # 检查请求头中的确认标志
                confirm_header = request.headers.get('X-Confirm-Action')
                if not confirm_header or confirm_header.lower() != 'true':
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"此操作为高危操作，请先确认: {action}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def get_high_risk_operations():
    """获取高危操作列表"""
    return HIGH_RISK_OPERATIONS