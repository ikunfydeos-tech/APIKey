# 重构版主程序 - 移除管理员功能
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import settings
from routers import auth_v2, keys_v2
from log_middleware import log_middleware
from pathlib import Path
import os

# 获取前端静态文件目录
FRONTEND_DIR = Path(__file__).parent.parent

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="LLM API Manager V2",
    description="API密钥管理系统 - 用户自主管理版",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
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

# Log middleware
@app.middleware("http")
async def log_middleware_wrapper(request: Request, call_next):
    return await log_middleware(request, call_next)

# Include routers
app.include_router(auth_v2.router)
app.include_router(keys_v2.router)

# Security headers
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
    return {"status": "healthy", "version": "2.0.0"}


# 挂载静态文件目录
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/images", StaticFiles(directory=FRONTEND_DIR / "images"), name="images")
app.mount("/icons", StaticFiles(directory=FRONTEND_DIR / "icons"), name="icons")


# 首页路由
@app.get("/")
async def read_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"error": "index.html not found"}


# 其他 HTML 页面路由
@app.get("/{page_name}.html")
async def read_page(page_name: str):
    # 安全检查：防止路径遍历攻击
    if ".." in page_name or "/" in page_name:
        return {"error": "Invalid page name"}
    
    # V2版本移除管理员页面
    if page_name == "admin":
        return {"error": "Admin page not available in V2"}
    
    page_file = FRONTEND_DIR / f"{page_name}.html"
    if page_file.exists():
        return FileResponse(page_file)
    return {"error": f"{page_name}.html not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
