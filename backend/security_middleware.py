"""
安全中间件模块

包含：
1. 动态管理员路径验证
2. 安全响应头设置
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from admin_path import verify_admin_api_access, get_admin_api_prefix, get_admin_path


async def admin_api_middleware(request: Request, call_next):
    """
    管理员 API 路径验证中间件
    
    确保只有正确的动态路径才能访问管理员 API
    """
    original_path = request.url.path
    
    # 允许 /api/admin-path 路径（获取管理员入口）
    if original_path == "/api/admin-path":
        return await call_next(request)
    
    # 阻止对旧固定路径 /api/admin/ 的访问（注意要有斜杠结尾）
    if original_path.startswith("/api/admin/") or original_path == "/api/admin":
        return JSONResponse(
            status_code=404,
            content={"detail": "Not Found"}
        )
    
    # 验证管理员 API 路径
    if original_path.startswith("/api/sec/"):
        if not verify_admin_api_access(original_path):
            return JSONResponse(
                status_code=404,
                content={"detail": "Not Found"}
            )
    
    return await call_next(request)


async def block_admin_page_access(request: Request, call_next):
    """
    阻止对固定 admin.html 的直接访问
    """
    original_path = request.url.path.lower()
    
    # 阻止常见的后台页面猜测
    blocked_patterns = [
        "/admin.html",
        "/admin",
        "/administrator",
        "/backend",
        "/console",
        "/control",
        "/manage",
        "/management",
        "/system",
        "/dashboard/admin",
    ]
    
    for pattern in blocked_patterns:
        if original_path == pattern or original_path == pattern + "/":
            return JSONResponse(
                status_code=404,
                content={"detail": "Not Found"}
            )
    
    return await call_next(request)


# 注意：get_admin_path 和 get_admin_api_prefix 函数
# 已移至 admin_path.py 模块，请直接从 admin_path 导入
