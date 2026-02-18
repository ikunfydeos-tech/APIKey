from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import settings
from routers import auth, keys, totp, payment
from routers import admin as admin_router
from log_middleware import log_middleware
from security_middleware import admin_api_middleware, block_admin_page_access
from admin_path import get_admin_path, get_admin_api_prefix, init_admin_path
from membership_service import start_scheduler, stop_scheduler
from pathlib import Path

# 初始化管理员路径（服务启动时）
admin_path = init_admin_path()
print(f"[Security] Admin path initialized: /sec/{admin_path}.html")
print(f"[Security] Admin API prefix: {get_admin_api_prefix()}")

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="LLM API Manager",
    description="API for managing multiple LLM provider API keys",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,  # 生产环境关闭 API 文档
    redoc_url="/redoc" if settings.DEBUG else None
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log middleware - 使用装饰器形式注册
@app.middleware("http")
async def log_middleware_wrapper(request: Request, call_next):
    return await log_middleware(request, call_next)

# Admin security middlewares - 使用装饰器形式注册
@app.middleware("http")
async def admin_api_middleware_wrapper(request: Request, call_next):
    return await admin_api_middleware(request, call_next)

@app.middleware("http")
async def block_admin_page_access_wrapper(request: Request, call_next):
    return await block_admin_page_access(request, call_next)

# Include public routers
app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(totp.router)
app.include_router(payment.router)  # 支付回调路由

# 动态注册管理员路由（使用动态前缀）
admin_api_prefix = get_admin_api_prefix()
app.include_router(admin_router.router, prefix=admin_api_prefix)

# 管理员路径获取端点（需要管理员身份验证）
from auth import get_current_admin_user
from models import User

@app.get("/api/admin-path")
async def get_admin_entry(current_user: User = Depends(get_current_admin_user)):
    """
    获取管理员入口路径
    只有管理员才能调用此接口
    """
    return {
        "admin_path": get_admin_path(),
        "admin_url": f"/sec/{get_admin_path()}.html",
        "success": True
    }

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """添加安全响应头"""
    response = await call_next(request)
    
    # 防止点击劫持
    response.headers["X-Frame-Options"] = "DENY"
    # 防止 MIME 类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"
    # XSS 防护
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # 引用策略
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # 禁止搜索引擎索引
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 启动会员检查定时任务
    start_scheduler()
    print("[Membership] 会员检查定时任务已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    # 停止定时任务
    stop_scheduler()
    print("[Membership] 会员检查定时任务已停止")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)