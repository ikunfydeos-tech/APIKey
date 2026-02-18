from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Request, HTTPException, status
from routers.auth import get_current_user
from models import LogEntry
import json
from pathlib import Path

def log_action(
    db: Session,
    user_id: int,
    username: str,
    action: str,
    resource_type: str = None,
    resource_id: int = None,
    resource_name: str = None,
    ip_address: str = None,
    user_agent: str = None,
    status: str = "success",
    error_message: str = None,
    details: dict = None
):
    """
    记录用户操作日志
    """
    try:
        log_entry = LogEntry(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
            details=json.dumps(details) if details else None
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Failed to log action: {e}")

async def log_middleware(request: Request, call_next):
    """
    全局中间件，记录所有请求的操作日志
    """
    from database import SessionLocal
    
    start_time = datetime.utcnow()
    response = None
    exception = None
    
    try:
        response = await call_next(request)
    except Exception as e:
        exception = e
        response = None
    
    # 只记录 API 路由的操作
    if request.url.path.startswith("/api/"):
        try:
            db = SessionLocal()
            current_user = None
            
            try:
                current_user = await get_current_user(request)
            except:
                pass
            
            # 获取客户端 IP
            x_forwarded_for = request.headers.get("X-Forwarded-For")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                x_real_ip = request.headers.get("X-Real-IP")
                if x_real_ip:
                    ip_address = x_real_ip
                else:
                    ip_address = request.client.host if request.client else "unknown"
            
            # 获取 User-Agent
            user_agent = request.headers.get("User-Agent", "")[:500] if request.headers.get("User-Agent") else ""
            
            # 构建日志详情
            details = {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "status_code": response.status_code if response else (500 if exception else None),
                "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }
            
            # 根据操作类型记录不同的日志
            action = "访问"
            resource_type = "SYSTEM"
            resource_id = None
            resource_name = "unknown"  # 初始化默认值，避免变量未定义错误
            
            if request.url.path.endswith("/login"):
                action = "登录"
                resource_type = "USER"
                if current_user:
                    resource_name = current_user.username
                else:
                    resource_name = request.query_params.get("username", "unknown")
            elif request.url.path.endswith("/logout"):
                action = "登出"
                resource_type = "USER"
                resource_name = current_user.username if current_user else "unknown"
            elif "/api/keys/" in request.url.path:
                if request.method == "POST":
                    action = "创建密钥"
                    resource_type = "API_KEY"
                    resource_name = request.query_params.get("key_name", "unknown")
                elif request.method == "PUT":
                    action = "更新密钥"
                    resource_type = "API_KEY"
                    key_id = request.url.path.split("/")[-1]
                    resource_id = int(key_id) if key_id.isdigit() else None
                    resource_name = request.query_params.get("key_name", "unknown")
                elif request.method == "DELETE":
                    action = "删除密钥"
                    resource_type = "API_KEY"
                    key_id = request.url.path.split("/")[-1]
                    resource_id = int(key_id) if key_id.isdigit() else None
                    resource_name = "unknown"
            
            # 记录日志
            log_action(
                db=db,
                user_id=current_user.id if current_user else None,
                username=current_user.username if current_user else None,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                ip_address=ip_address,
                user_agent=user_agent,
                status="success" if (response and response.status_code < 400) or (not response and not exception) else "failed",
                error_message=str(exception) if exception else None,
                details=details
            )
            
            db.close()
        except Exception as e:
            print(f"Failed to log request: {e}")
    
    if exception:
        raise exception
    
    return response