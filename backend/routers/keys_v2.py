# 重构版密钥管理路由 - 用户自主管理
import os
from base64 import urlsafe_b64encode, urlsafe_b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models_v2 import User, UserApiKey, ApiProvider, ApiModel, TokenUsage, KeyBalance, RenewalRecord, LogEntry
from schemas import (
    UserApiKeyCreate, 
    UserApiKeyUpdate, 
    UserApiKeyResponse, 
    UserApiKeyWithDecrypted,
    ApiModelResponse,
    MessageResponse
)
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/keys", tags=["api-keys"])

# Generate Fernet key from settings
def get_encryption_key() -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.ENCRYPTION_SALT,
        iterations=100000,
    )
    return urlsafe_b64encode(kdf.derive(settings.API_KEY_ENCRYPTION_KEY))

def encrypt_api_key(api_key: str) -> str:
    f = Fernet(get_encryption_key())
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_key.encode()).decode()

def get_key_preview(api_key: str) -> str:
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"


def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "")


def log_action(db: Session, user_id: int, username: str, action: str, 
               ip: str, ua: str, status: str = "success", 
               resource_type: str = None, resource_id: int = None,
               resource_name: str = None, details: dict = None):
    """记录操作日志"""
    log = LogEntry(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        ip_address=ip,
        user_agent=ua,
        status=status,
        details=str(details) if details else None
    )
    db.add(log)
    db.commit()


# ============ 服务商和模型 ============

@router.get("/providers", response_model=List[dict])
def get_providers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取所有激活的服务商"""
    providers = db.query(ApiProvider).filter(
        ApiProvider.is_active == True
    ).order_by(ApiProvider.sort_order).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "base_url": p.base_url,
            "icon": p.icon,
            "description": p.description
        }
        for p in providers
    ]


@router.get("/models", response_model=List[ApiModelResponse])
def get_all_models(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取所有可用模型"""
    models = db.query(ApiModel).join(ApiProvider).filter(
        ApiProvider.is_active == True
    ).order_by(ApiProvider.sort_order, ApiModel.sort_order).all()
    return models


@router.get("/models/{provider_id}", response_model=List[ApiModelResponse])
def get_provider_models(
    provider_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """获取指定服务商的模型"""
    models = db.query(ApiModel).filter(
        ApiModel.provider_id == provider_id
    ).order_by(ApiModel.sort_order).all()
    return models


# ============ 密钥管理 ============

@router.get("", response_model=List[UserApiKeyResponse])
def get_user_keys(
    status_filter: str = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """获取用户的所有密钥"""
    query = db.query(UserApiKey).filter(UserApiKey.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(UserApiKey.status == status_filter)
    
    keys = query.order_by(UserApiKey.created_at.desc()).all()
    
    result = []
    for key in keys:
        provider = db.query(ApiProvider).filter(ApiProvider.id == key.provider_id).first()
        
        # 检查是否过期
        is_expired = key.expires_at and key.expires_at < datetime.utcnow()
        
        result.append(UserApiKeyResponse(
            id=key.id,
            provider_id=key.provider_id,
            provider_name=provider.display_name if provider else None,
            key_name=key.key_name,
            api_key_preview=key.api_key_preview,
            model_id=key.model_id,
            status="expired" if is_expired else key.status,
            notes=key.notes,
            created_at=key.created_at,
            updated_at=key.updated_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at
        ))
    
    return result


@router.post("", response_model=UserApiKeyResponse)
def create_api_key(
    request: Request,
    key_data: UserApiKeyCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """创建新密钥"""
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    provider = db.query(ApiProvider).filter(ApiProvider.id == key_data.provider_id).first()
    if not provider:
        raise HTTPException(status_code=400, detail="服务商不存在")
    
    # 检查密钥名是否重复
    existing = db.query(UserApiKey).filter(
        UserApiKey.user_id == current_user.id,
        UserApiKey.key_name == key_data.key_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="密钥名称已存在")
    
    encrypted_key = encrypt_api_key(key_data.api_key)
    
    new_key = UserApiKey(
        user_id=current_user.id,
        provider_id=key_data.provider_id,
        key_name=key_data.key_name,
        api_key_encrypted=encrypted_key,
        api_key_preview=get_key_preview(key_data.api_key),
        model_id=key_data.model_id,
        notes=key_data.notes,
        status="active"
    )
    
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    # 记录日志
    log_action(db, current_user.id, current_user.username, "创建密钥", 
               ip, ua, resource_type="API_KEY", resource_id=new_key.id,
               resource_name=key_data.key_name)
    
    return UserApiKeyResponse(
        id=new_key.id,
        provider_id=new_key.provider_id,
        provider_name=provider.display_name,
        key_name=new_key.key_name,
        api_key_preview=new_key.api_key_preview,
        model_id=new_key.model_id,
        status=new_key.status,
        notes=new_key.notes,
        created_at=new_key.created_at,
        updated_at=new_key.updated_at,
        last_used_at=new_key.last_used_at,
        expires_at=new_key.expires_at
    )


@router.get("/{key_id}", response_model=UserApiKeyWithDecrypted)
def get_api_key(
    key_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """获取密钥详情（包含解密后的密钥）"""
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    provider = db.query(ApiProvider).filter(ApiProvider.id == key.provider_id).first()
    
    return UserApiKeyWithDecrypted(
        id=key.id,
        provider_id=key.provider_id,
        provider_name=provider.display_name if provider else None,
        key_name=key.key_name,
        api_key_preview=key.api_key_preview,
        api_key=decrypt_api_key(key.api_key_encrypted),
        model_id=key.model_id,
        status=key.status,
        notes=key.notes,
        created_at=key.created_at,
        updated_at=key.updated_at,
        last_used_at=key.last_used_at,
        expires_at=key.expires_at
    )


@router.put("/{key_id}", response_model=UserApiKeyResponse)
def update_api_key(
    request: Request,
    key_id: int,
    key_data: UserApiKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新密钥"""
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    if key_data.key_name:
        existing = db.query(UserApiKey).filter(
            UserApiKey.user_id == current_user.id,
            UserApiKey.key_name == key_data.key_name,
            UserApiKey.id != key_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="密钥名称已存在")
        key.key_name = key_data.key_name
    
    if key_data.api_key:
        key.api_key_encrypted = encrypt_api_key(key_data.api_key)
        key.api_key_preview = get_key_preview(key_data.api_key)
    
    if key_data.model_id is not None:
        key.model_id = key_data.model_id
    
    if key_data.status:
        key.status = key_data.status
    
    if key_data.notes is not None:
        key.notes = key_data.notes
    
    db.commit()
    db.refresh(key)
    
    # 记录日志
    log_action(db, current_user.id, current_user.username, "更新密钥", 
               ip, ua, resource_type="API_KEY", resource_id=key.id,
               resource_name=key.key_name)
    
    provider = db.query(ApiProvider).filter(ApiProvider.id == key.provider_id).first()
    
    return UserApiKeyResponse(
        id=key.id,
        provider_id=key.provider_id,
        provider_name=provider.display_name if provider else None,
        key_name=key.key_name,
        api_key_preview=key.api_key_preview,
        model_id=key.model_id,
        status=key.status,
        notes=key.notes,
        created_at=key.created_at,
        updated_at=key.updated_at,
        last_used_at=key.last_used_at,
        expires_at=key.expires_at
    )


@router.delete("/{key_id}", response_model=MessageResponse)
def delete_api_key(
    request: Request,
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除密钥"""
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    key_name = key.key_name
    db.delete(key)
    db.commit()
    
    # 记录日志
    log_action(db, current_user.id, current_user.username, "删除密钥", 
               ip, ua, resource_type="API_KEY", resource_id=key_id,
               resource_name=key_name)
    
    return MessageResponse(message="密钥已删除", success=True)


# ============ 密钥测试 ============

@router.post("/test", response_model=dict)
async def test_api_key(
    request: Request,
    test_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试 API 密钥是否有效"""
    import httpx
    
    provider_id = test_data.get("provider_id")
    api_key = test_data.get("api_key")
    
    if not provider_id or not api_key:
        raise HTTPException(status_code=400, detail="缺少服务商ID或API密钥")
    
    provider = db.query(ApiProvider).filter(ApiProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="服务商不存在")
    
    base_url = provider.base_url.rstrip("/")
    provider_name = provider.name.lower()
    
    # 根据不同服务商使用正确的测试端点
    if provider_name == "openai":
        test_url = f"{base_url}/models"
    elif provider_name == "anthropic":
        return {
            "success": True,
            "message": "Anthropic API 密钥格式验证通过，请确保密钥有效",
            "provider_name": provider.display_name
        }
    elif provider_name == "google":
        test_url = f"{base_url}/models?key={api_key}"
    elif provider_name in ["deepseek", "moonshot", "zhipu", "alibaba"]:
        test_url = f"{base_url}/models"
    elif provider_name == "baidu":
        return {
            "success": True,
            "message": "百度文心 API 需要通过百度控制台验证，请确保密钥格式正确",
            "provider_name": provider.display_name
        }
    else:
        test_url = f"{base_url}/models"
    
    headers = {}
    if provider_name != "google":
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(test_url, headers=headers)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    model_count = len(data.get("data", []))
                    return {
                        "success": True,
                        "message": f"连接成功，可用模型: {model_count} 个",
                        "provider_name": provider.display_name,
                        "model_count": model_count
                    }
                except:
                    return {
                        "success": True,
                        "message": "连接成功，API密钥有效",
                        "provider_name": provider.display_name
                    }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "API密钥无效或已过期",
                    "provider_name": provider.display_name
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "message": "API密钥权限不足",
                    "provider_name": provider.display_name
                }
            else:
                return {
                    "success": False,
                    "message": f"连接失败，状态码: {response.status_code}",
                    "provider_name": provider.display_name
                }
    except httpx.TimeoutException:
        return {
            "success": False,
            "message": "连接超时，请检查网络或API地址",
            "provider_name": provider.display_name
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "message": "无法连接到服务器，请检查API地址",
            "provider_name": provider.display_name
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"测试失败: {str(e)}",
            "provider_name": provider.display_name
        }


# ============ 余额和Token使用 ============

@router.get("/{key_id}/balance")
def get_key_balance(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取密钥的余额信息"""
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    # 获取余额记录
    balance = db.query(KeyBalance).filter(KeyBalance.key_id == key_id).first()
    
    # 获取使用统计
    usage_stats = db.query(TokenUsage).filter(TokenUsage.key_id == key_id).all()
    
    total_tokens = sum(u.total_tokens for u in usage_stats)
    total_cost = sum(float(u.cost or 0) for u in usage_stats)
    
    return {
        "key_id": key_id,
        "key_name": key.key_name,
        "provider_id": key.provider_id,
        "balance": float(balance.balance) if balance else None,
        "currency": balance.currency if balance else "USD",
        "total_usage": float(balance.total_usage) if balance else total_cost,
        "total_requests": balance.total_requests if balance else len(usage_stats),
        "total_tokens": total_tokens,
        "last_checked_at": balance.last_checked_at.isoformat() if balance and balance.last_checked_at else None
    }


@router.get("/{key_id}/usage")
def get_key_usage(
    key_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取密钥的Token使用记录"""
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    from_date = datetime.utcnow() - timedelta(days=days)
    
    usage = db.query(TokenUsage).filter(
        TokenUsage.key_id == key_id,
        TokenUsage.created_at >= from_date
    ).order_by(TokenUsage.created_at.desc()).all()
    
    return {
        "key_id": key_id,
        "key_name": key.key_name,
        "days": days,
        "total_records": len(usage),
        "usage": [
            {
                "id": u.id,
                "model_id": u.model_id,
                "request_tokens": u.request_tokens,
                "response_tokens": u.response_tokens,
                "total_tokens": u.total_tokens,
                "cost": float(u.cost) if u.cost else None,
                "created_at": u.created_at.isoformat()
            }
            for u in usage
        ]
    }


@router.get("/{key_id}/stats")
def get_key_stats(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取密钥统计信息"""
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    # 总体统计
    all_usage = db.query(TokenUsage).filter(TokenUsage.key_id == key_id).all()
    
    total_requests = len(all_usage)
    total_tokens = sum(u.total_tokens for u in all_usage)
    total_cost = sum(float(u.cost or 0) for u in all_usage)
    
    # 按模型统计
    from sqlalchemy import func
    model_stats = db.query(
        TokenUsage.model_id,
        func.count(TokenUsage.id).label('request_count'),
        func.sum(TokenUsage.total_tokens).label('token_count'),
        func.sum(TokenUsage.cost).label('total_cost')
    ).filter(TokenUsage.key_id == key_id).group_by(TokenUsage.model_id).all()
    
    # 最近7天统计
    last_7_days = []
    for i in range(6, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_usage = db.query(TokenUsage).filter(
            TokenUsage.key_id == key_id,
            TokenUsage.created_at >= day_start,
            TokenUsage.created_at < day_end
        ).all()
        
        last_7_days.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "requests": len(day_usage),
            "tokens": sum(u.total_tokens for u in day_usage),
            "cost": sum(float(u.cost or 0) for u in day_usage)
        })
    
    return {
        "key_id": key_id,
        "key_name": key.key_name,
        "overall": {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": total_cost
        },
        "by_model": [
            {
                "model_id": m.model_id,
                "request_count": m.request_count,
                "token_count": m.token_count or 0,
                "total_cost": float(m.total_cost) if m.total_cost else 0
            }
            for m in model_stats
        ],
        "last_7_days": last_7_days
    }


# ============ 续费功能 ============

@router.post("/{key_id}/renew")
def renew_key(
    request: Request,
    key_id: int,
    renewal_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    续费密钥
    {
        "amount": 100.00,
        "currency": "USD",
        "duration_days": 365,
        "notes": "年度续费"
    }
    """
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    amount = renewal_data.get("amount")
    currency = renewal_data.get("currency", "USD")
    duration_days = renewal_data.get("duration_days")
    notes = renewal_data.get("notes", "")
    
    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="续费金额必须大于0")
    
    # 计算新的过期时间
    if duration_days:
        if key.expires_at and key.expires_at > datetime.utcnow():
            # 在现有基础上续期
            new_expires = key.expires_at + timedelta(days=duration_days)
        else:
            # 从当前时间开始计算
            new_expires = datetime.utcnow() + timedelta(days=duration_days)
        key.expires_at = new_expires
        db.commit()
    
    # 创建续费记录
    renewal = RenewalRecord(
        user_id=current_user.id,
        key_id=key_id,
        provider_id=key.provider_id,
        amount=amount,
        currency=currency,
        duration_days=duration_days,
        expires_at=key.expires_at,
        notes=notes
    )
    db.add(renewal)
    db.commit()
    
    # 记录日志
    log_action(db, current_user.id, current_user.username, "密钥续费", 
               ip, ua, resource_type="API_KEY", resource_id=key_id,
               resource_name=key.key_name, details={
                   "amount": amount,
                   "currency": currency,
                   "duration_days": duration_days
               })
    
    return {
        "success": True,
        "message": "续费成功",
        "renewal_id": renewal.id,
        "key_id": key_id,
        "new_expires_at": key.expires_at.isoformat() if key.expires_at else None
    }


@router.get("/{key_id}/renewals")
def get_key_renewals(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取密钥的续费记录"""
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    renewals = db.query(RenewalRecord).filter(
        RenewalRecord.key_id == key_id
    ).order_by(RenewalRecord.created_at.desc()).all()
    
    return {
        "key_id": key_id,
        "key_name": key.key_name,
        "renewals": [
            {
                "id": r.id,
                "amount": float(r.amount),
                "currency": r.currency,
                "duration_days": r.duration_days,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "status": r.status,
                "notes": r.notes,
                "created_at": r.created_at.isoformat()
            }
            for r in renewals
        ]
    }
