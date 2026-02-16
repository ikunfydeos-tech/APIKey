from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import settings
from routers import auth, keys, admin
from pathlib import Path

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

# Include routers
app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(admin.router)

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
    
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
