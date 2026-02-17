"""
动态管理员路径管理模块

安全策略：
1. 服务启动时生成随机管理员路径（12位随机字符）
2. 管理员 API 使用动态前缀
3. 只有验证通过的管理员才能获取完整路径
4. 路径在服务重启后重新生成
"""
import secrets
import string
from typing import Optional
from functools import lru_cache

# 生成长度
ADMIN_PATH_LENGTH = 16

# 全局存储当前管理员路径
_ADMIN_PATH: Optional[str] = None
_ADMIN_API_PREFIX: Optional[str] = None


def generate_secure_path(length: int = ADMIN_PATH_LENGTH) -> str:
    """
    生成安全的随机路径
    使用 secrets 模块确保密码学安全
    """
    # 使用字母和数字，避免易混淆字符
    chars = string.ascii_lowercase + string.digits
    # 排除易混淆字符
    chars = chars.replace('l', '').replace('1', '').replace('o', '').replace('0', '')
    return ''.join(secrets.choice(chars) for _ in range(length))


def init_admin_path() -> str:
    """
    初始化管理员路径（服务启动时调用）
    返回生成的路径
    """
    global _ADMIN_PATH, _ADMIN_API_PREFIX
    
    _ADMIN_PATH = generate_secure_path()
    _ADMIN_API_PREFIX = f"/api/sec/{_ADMIN_PATH}"
    
    return _ADMIN_PATH


def get_admin_path() -> str:
    """
    获取当前管理员页面路径
    如果未初始化则自动初始化
    """
    global _ADMIN_PATH
    if _ADMIN_PATH is None:
        init_admin_path()
    return _ADMIN_PATH


def get_admin_api_prefix() -> str:
    """
    获取当前管理员 API 前缀
    如果未初始化则自动初始化
    """
    global _ADMIN_API_PREFIX
    if _ADMIN_API_PREFIX is None:
        init_admin_path()
    return _ADMIN_API_PREFIX


def get_admin_page_url(base_url: str = "") -> str:
    """
    获取管理员页面完整 URL
    管理员页面将重命名为动态名称
    """
    path = get_admin_path()
    return f"{base_url}/sec/{path}.html"


def verify_admin_access(request_path: str) -> bool:
    """
    验证请求路径是否匹配管理员路径
    """
    admin_path = get_admin_path()
    # 检查是否是管理员路径请求
    return request_path == f"/sec/{admin_path}" or request_path == f"/sec/{admin_path}.html"


def verify_admin_api_access(request_path: str) -> bool:
    """
    验证请求路径是否匹配管理员 API 前缀
    """
    admin_prefix = get_admin_api_prefix()
    return request_path.startswith(admin_prefix)


# 服务启动时自动初始化
init_admin_path()
