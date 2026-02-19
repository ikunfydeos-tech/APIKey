"""
用户自助功能路由
- 日志查看
- 登录历史
- Token使用记录
- 余额管理
- 续费功能
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from pydantic import BaseModel
from database import get_db
from models_v2 import (
    User, UserApiKey, ApiProvider, LogEntry, LoginHistory, 
    TokenUsage, KeyBalance, RenewalRecord
)
from auth import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/user", tags=["user"])
limiter = Limiter(key_func=get_remote_address)


# ============ 请求模型 ============

class RenewKeyRequest(BaseModel):
    """续费请求"""
    key_id: int
    amount: float
    duration_days: int = 30
    notes: Optional[str] = None


# ============ 辅助函数 ============

def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def log_action(db: Session, user_id: int, username: str, action: str, 
               ip: str, status: str = "success", resource_type: str = None,
               resource_id: int = None, resource_name: str = None, details: str = None):
    """记录操作日志"""
    log = LogEntry(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        ip_address=ip,
        status=status,
        details=details
    )
    db.add(log)
    db.commit()


# ============ 仪表盘统计 ============

@router.get("/dashboard")
def get_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户仪表盘数据"""
    # API密钥统计
    total_keys = db.query(UserApiKey).filter(UserApiKey.user_id == current_user.id).count()
    active_keys = db.query(UserApiKey).filter(
        UserApiKey.user_id == current_user.id,
        UserApiKey.status == "active"
    ).count()
    
    # 今日Token使用
    today = datetime.utcnow().date()
    today_usage = db.query(func.sum(TokenUsage.total_tokens)).filter(
        TokenUsage.user_id == current_user.id,
        func.date(TokenUsage.created_at) == today
    ).scalar() or 0
    
    # 本月Token使用
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_usage = db.query(func.sum(TokenUsage.total_tokens)).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.created_at >= month_start
    ).scalar() or 0
    
    # 总Token使用
    total_usage = db.query(func.sum(TokenUsage.total_tokens)).filter(
        TokenUsage.user_id == current_user.id
    ).scalar() or 0
    
    # 近7天趋势
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_usage = db.query(
        func.date(TokenUsage.created_at).label('date'),
        func.sum(TokenUsage.total_tokens).label('tokens')
    ).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.created_at >= seven_days_ago
    ).group_by(func.date(TokenUsage.created_at)).all()
    
    # 按模型使用统计
    model_usage = db.query(
        TokenUsage.model_id,
        func.sum(TokenUsage.total_tokens).label('tokens'),
        func.count(TokenUsage.id).label('requests')
    ).filter(
        TokenUsage.user_id == current_user.id
    ).group_by(TokenUsage.model_id).order_by(desc('tokens')).limit(10).all()
    
    # 最近登录记录
    recent_logins = db.query(LoginHistory).filter(
        LoginHistory.user_id == current_user.id
    ).order_by(desc(LoginHistory.created_at)).limit(5).all()
    
    return {
        "keys": {
            "total": total_keys,
            "active": active_keys
        },
        "tokens": {
            "today": today_usage,
            "month": month_usage,
            "total": total_usage
        },
        "daily_trend": [
            {"date": str(d.date), "tokens": d.tokens} 
            for d in daily_usage
        ],
        "model_usage": [
            {"model": m.model_id, "tokens": m.tokens, "requests": m.requests}
            for m in model_usage
        ],
        "recent_logins": [
            {
                "ip": l.ip_address,
                "location": l.location,
                "status": l.status,
                "time": l.created_at.isoformat() if l.created_at else None
            }
            for l in recent_logins
        ]
    }


# ============ 登录历史 ============

@router.get("/login-history")
def get_login_history(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取登录历史记录"""
    query = db.query(LoginHistory).filter(LoginHistory.user_id == current_user.id)
    
    if status:
        query = query.filter(LoginHistory.status == status)
    
    total = query.count()
    
    history = query.order_by(desc(LoginHistory.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": h.id,
                "ip_address": h.ip_address,
                "location": h.location,
                "user_agent": h.user_agent,
                "login_type": h.login_type,
                "status": h.status,
                "fail_reason": h.fail_reason,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in history
        ]
    }


@router.get("/login-stats")
def get_login_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取登录统计"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 总登录次数
    total_logins = db.query(LoginHistory).filter(
        LoginHistory.user_id == current_user.id,
        LoginHistory.created_at >= start_date
    ).count()
    
    # 成功/失败次数
    success_logins = db.query(LoginHistory).filter(
        LoginHistory.user_id == current_user.id,
        LoginHistory.created_at >= start_date,
        LoginHistory.status == "success"
    ).count()
    
    failed_logins = total_logins - success_logins
    
    # 唯一IP数
    unique_ips = db.query(func.count(func.distinct(LoginHistory.ip_address))).filter(
        LoginHistory.user_id == current_user.id,
        LoginHistory.created_at >= start_date
    ).scalar() or 0
    
    # 按日期统计
    daily_logins = db.query(
        func.date(LoginHistory.created_at).label('date'),
        func.count().label('count')
    ).filter(
        LoginHistory.user_id == current_user.id,
        LoginHistory.created_at >= start_date
    ).group_by(func.date(LoginHistory.created_at)).all()
    
    return {
        "period_days": days,
        "total_logins": total_logins,
        "success_logins": success_logins,
        "failed_logins": failed_logins,
        "unique_ips": unique_ips,
        "daily_logins": [{"date": str(d.date), "count": d.count} for d in daily_logins]
    }


# ============ 操作日志 ============

@router.get("/logs")
def get_user_logs(
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户操作日志"""
    query = db.query(LogEntry).filter(LogEntry.user_id == current_user.id)
    
    if action:
        query = query.filter(LogEntry.action.ilike(f"%{action}%"))
    if status:
        query = query.filter(LogEntry.status == status)
    
    total = query.count()
    
    logs = query.order_by(desc(LogEntry.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address,
                "status": log.status,
                "error_message": log.error_message,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    }


@router.get("/log-actions")
def get_log_action_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取操作类型列表"""
    actions = db.query(func.distinct(LogEntry.action)).filter(
        LogEntry.user_id == current_user.id
    ).all()
    
    return [a[0] for a in actions if a[0]]


# ============ Token使用记录 ============

@router.get("/token-usage")
def get_token_usage(
    page: int = 1,
    page_size: int = 20,
    key_id: Optional[int] = None,
    model_id: Optional[str] = None,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取Token使用记录"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(TokenUsage).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.created_at >= start_date
    )
    
    if key_id:
        query = query.filter(TokenUsage.key_id == key_id)
    if model_id:
        query = query.filter(TokenUsage.model_id == model_id)
    
    total = query.count()
    
    usage = query.order_by(desc(TokenUsage.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": u.id,
                "key_id": u.key_id,
                "key_name": u.key.key_name if u.key else None,
                "provider": u.provider.display_name if u.provider else None,
                "model_id": u.model_id,
                "request_tokens": u.request_tokens,
                "response_tokens": u.response_tokens,
                "total_tokens": u.total_tokens,
                "cost": float(u.cost) if u.cost else None,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in usage
        ]
    }


@router.get("/token-stats")
def get_token_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取Token使用统计"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 总使用量
    total_usage = db.query(
        func.sum(TokenUsage.request_tokens).label('request'),
        func.sum(TokenUsage.response_tokens).label('response'),
        func.sum(TokenUsage.total_tokens).label('total'),
        func.sum(TokenUsage.cost).label('cost'),
        func.count(TokenUsage.id).label('requests')
    ).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.created_at >= start_date
    ).first()
    
    # 按密钥统计
    by_key = db.query(
        TokenUsage.key_id,
        UserApiKey.key_name,
        func.sum(TokenUsage.total_tokens).label('tokens'),
        func.count(TokenUsage.id).label('requests')
    ).join(UserApiKey).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.created_at >= start_date
    ).group_by(TokenUsage.key_id, UserApiKey.key_name).all()
    
    # 按模型统计
    by_model = db.query(
        TokenUsage.model_id,
        func.sum(TokenUsage.total_tokens).label('tokens'),
        func.count(TokenUsage.id).label('requests')
    ).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.created_at >= start_date
    ).group_by(TokenUsage.model_id).all()
    
    # 按服务商统计
    by_provider = db.query(
        ApiProvider.display_name,
        func.sum(TokenUsage.total_tokens).label('tokens'),
        func.count(TokenUsage.id).label('requests')
    ).join(TokenUsage).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.created_at >= start_date
    ).group_by(ApiProvider.id, ApiProvider.display_name).all()
    
    # 每日趋势
    daily = db.query(
        func.date(TokenUsage.created_at).label('date'),
        func.sum(TokenUsage.total_tokens).label('tokens'),
        func.count(TokenUsage.id).label('requests')
    ).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.created_at >= start_date
    ).group_by(func.date(TokenUsage.created_at)).all()
    
    return {
        "period_days": days,
        "summary": {
            "request_tokens": total_usage.request or 0,
            "response_tokens": total_usage.response or 0,
            "total_tokens": total_usage.total or 0,
            "total_cost": float(total_usage.cost) if total_usage.cost else 0,
            "total_requests": total_usage.requests or 0
        },
        "by_key": [
            {"key_id": k.key_id, "key_name": k.key_name, "tokens": k.tokens, "requests": k.requests}
            for k in by_key
        ],
        "by_model": [
            {"model": m.model_id, "tokens": m.tokens, "requests": m.requests}
            for m in by_model
        ],
        "by_provider": [
            {"provider": p.display_name, "tokens": p.tokens, "requests": p.requests}
            for p in by_provider
        ],
        "daily_trend": [
            {"date": str(d.date), "tokens": d.tokens, "requests": d.requests}
            for d in daily
        ]
    }


# ============ 余额管理 ============

@router.get("/balances")
def get_key_balances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有密钥余额"""
    # 获取用户所有密钥及其余额
    keys = db.query(UserApiKey).filter(
        UserApiKey.user_id == current_user.id
    ).all()
    
    result = []
    for key in keys:
        balance = db.query(KeyBalance).filter(
            KeyBalance.key_id == key.id
        ).first()
        
        result.append({
            "key_id": key.id,
            "key_name": key.key_name,
            "provider": key.provider.display_name if key.provider else None,
            "status": key.status,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "balance": float(balance.balance) if balance and balance.balance else None,
            "currency": balance.currency if balance else "USD",
            "total_usage": float(balance.total_usage) if balance and balance.total_usage else 0,
            "total_requests": balance.total_requests if balance else 0,
            "last_checked": balance.last_checked_at.isoformat() if balance and balance.last_checked_at else None
        })
    
    return result


@router.get("/balances/{key_id}")
def get_key_balance(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个密钥余额详情"""
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    balance = db.query(KeyBalance).filter(
        KeyBalance.key_id == key_id
    ).first()
    
    return {
        "key_id": key.id,
        "key_name": key.key_name,
        "provider": key.provider.display_name if key.provider else None,
        "status": key.status,
        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        "balance": float(balance.balance) if balance and balance.balance else None,
        "currency": balance.currency if balance else "USD",
        "total_usage": float(balance.total_usage) if balance and balance.total_usage else 0,
        "total_requests": balance.total_requests if balance else 0,
        "last_checked": balance.last_checked_at.isoformat() if balance and balance.last_checked_at else None
    }


# ============ 续费功能 ============

@router.post("/renew")
def renew_key(
    request: Request,
    data: RenewKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """续费密钥"""
    # 验证密钥归属
    key = db.query(UserApiKey).filter(
        UserApiKey.id == data.key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="密钥不存在")
    
    if key.status != "active":
        raise HTTPException(status_code=400, detail="只能续费有效状态的密钥")
    
    # 创建续费记录
    new_expires_at = None
    if data.duration_days > 0:
        if key.expires_at and key.expires_at > datetime.utcnow():
            new_expires_at = key.expires_at + timedelta(days=data.duration_days)
        else:
            new_expires_at = datetime.utcnow() + timedelta(days=data.duration_days)
    
    renewal = RenewalRecord(
        user_id=current_user.id,
        key_id=key.id,
        provider_id=key.provider_id,
        amount=data.amount,
        duration_days=data.duration_days,
        expires_at=new_expires_at,
        notes=data.notes
    )
    db.add(renewal)
    
    # 更新密钥过期时间
    if new_expires_at:
        key.expires_at = new_expires_at
        key.updated_at = datetime.utcnow()
    
    # 更新余额
    balance = db.query(KeyBalance).filter(KeyBalance.key_id == key.id).first()
    if balance:
        if balance.balance:
            balance.balance = float(balance.balance) + data.amount
        else:
            balance.balance = data.amount
        balance.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(renewal)
    
    # 记录日志
    ip = get_client_ip(request)
    log_action(
        db, current_user.id, current_user.username, "续费密钥",
        ip, "success", "key", key.id, key.key_name,
        f"金额: {data.amount}, 天数: {data.duration_days}"
    )
    
    return {
        "success": True,
        "message": "续费成功",
        "renewal": {
            "id": renewal.id,
            "amount": float(renewal.amount),
            "duration_days": renewal.duration_days,
            "new_expires_at": renewal.expires_at.isoformat() if renewal.expires_at else None,
            "created_at": renewal.created_at.isoformat()
        }
    }


@router.get("/renewals")
def get_renewal_records(
    page: int = 1,
    page_size: int = 20,
    key_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取续费记录"""
    query = db.query(RenewalRecord).filter(
        RenewalRecord.user_id == current_user.id
    )
    
    if key_id:
        query = query.filter(RenewalRecord.key_id == key_id)
    
    total = query.count()
    
    records = query.order_by(desc(RenewalRecord.created_at))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": r.id,
                "key_id": r.key_id,
                "key_name": r.key.key_name if r.key else None,
                "provider": r.provider.display_name if r.provider else None,
                "amount": float(r.amount),
                "currency": r.currency,
                "duration_days": r.duration_days,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "status": r.status,
                "notes": r.notes,
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]
    }


@router.get("/renewals/summary")
def get_renewal_summary(
    months: int = 12,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取续费汇总"""
    start_date = datetime.utcnow() - timedelta(days=months * 30)
    
    # 总续费金额
    total_amount = db.query(func.sum(RenewalRecord.amount)).filter(
        RenewalRecord.user_id == current_user.id,
        RenewalRecord.created_at >= start_date
    ).scalar() or 0
    
    # 续费次数
    total_renewals = db.query(RenewalRecord).filter(
        RenewalRecord.user_id == current_user.id,
        RenewalRecord.created_at >= start_date
    ).count()
    
    # 按密钥统计
    by_key = db.query(
        RenewalRecord.key_id,
        UserApiKey.key_name,
        func.sum(RenewalRecord.amount).label('total'),
        func.count(RenewalRecord.id).label('count')
    ).join(UserApiKey).filter(
        RenewalRecord.user_id == current_user.id,
        RenewalRecord.created_at >= start_date
    ).group_by(RenewalRecord.key_id, UserApiKey.key_name).all()
    
    # 按月份统计
    by_month = db.query(
        func.strftime('%Y-%m', RenewalRecord.created_at).label('month'),
        func.sum(RenewalRecord.amount).label('total'),
        func.count(RenewalRecord.id).label('count')
    ).filter(
        RenewalRecord.user_id == current_user.id,
        RenewalRecord.created_at >= start_date
    ).group_by(func.strftime('%Y-%m', RenewalRecord.created_at)).all()
    
    return {
        "period_months": months,
        "total_amount": float(total_amount),
        "total_renewals": total_renewals,
        "by_key": [
            {"key_id": k.key_id, "key_name": k.key_name, "total": float(k.total), "count": k.count}
            for k in by_key
        ],
        "by_month": [
            {"month": m.month, "total": float(m.total), "count": m.count}
            for m in by_month
        ]
    }
