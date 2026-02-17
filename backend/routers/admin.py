import json
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from database import get_db
from models import ApiProvider, ApiModel, UserApiKey
from schemas import MessageResponse
from auth import get_current_admin_user
from models import User
from config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============ 数据统计 ============

@router.get("/stats/overview")
def get_stats_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统数据概览"""
    # 用户统计
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_count = db.query(User).filter(User.role == "admin").count()
    
    # 今日新增用户
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    new_users_today = db.query(User).filter(User.created_at >= today_start).count()
    
    # 密钥统计
    total_keys = db.query(UserApiKey).count()
    active_keys = db.query(UserApiKey).filter(UserApiKey.status == "active").count()
    
    # 今日新增密钥
    new_keys_today = db.query(UserApiKey).filter(UserApiKey.created_at >= today_start).count()
    
    # 服务商统计
    total_providers = db.query(ApiProvider).count()
    active_providers = db.query(ApiProvider).filter(ApiProvider.is_active == True).count()
    
    # 模型统计
    total_models = db.query(ApiModel).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_count,
            "new_today": new_users_today
        },
        "keys": {
            "total": total_keys,
            "active": active_keys,
            "new_today": new_keys_today
        },
        "providers": {
            "total": total_providers,
            "active": active_providers
        },
        "models": {
            "total": total_models
        }
    }

@router.get("/stats/providers")
def get_provider_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取各服务商密钥分布统计"""
    stats = db.query(
        ApiProvider.display_name,
        func.count(UserApiKey.id).label("key_count")
    ).outerjoin(
        UserApiKey, ApiProvider.id == UserApiKey.provider_id
    ).filter(
        ApiProvider.is_active == True
    ).group_by(
        ApiProvider.id, ApiProvider.display_name
    ).order_by(
        desc("key_count")
    ).all()
    
    return [
        {"provider": s.display_name or "未知", "count": s.key_count}
        for s in stats
    ]

@router.get("/stats/registration-trend")
def get_registration_trend(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取用户注册趋势"""
    result = []
    today = datetime.utcnow().date()
    
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        user_count = db.query(User).filter(
            User.created_at >= date_start,
            User.created_at <= date_end
        ).count()
        
        key_count = db.query(UserApiKey).filter(
            UserApiKey.created_at >= date_start,
            UserApiKey.created_at <= date_end
        ).count()
        
        result.append({
            "date": date.isoformat(),
            "users": user_count,
            "keys": key_count
        })
    
    return result


# ============ 用户管理 ============

@router.get("/users")
def get_users(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取用户列表"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status == "active":
        query = query.filter(User.is_active == True)
    elif status == "inactive":
        query = query.filter(User.is_active == False)
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # 获取每个用户的密钥数量
    user_list = []
    for user in users:
        key_count = db.query(UserApiKey).filter(UserApiKey.user_id == user.id).count()
        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "key_count": key_count
        })
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": user_list
    }

@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取用户的密钥列表
    keys = db.query(UserApiKey).filter(UserApiKey.user_id == user_id).all()
    keys_list = []
    for key in keys:
        provider = db.query(ApiProvider).filter(ApiProvider.id == key.provider_id).first()
        keys_list.append({
            "id": key.id,
            "provider_name": provider.display_name if provider else "未知",
            "key_name": key.key_name,
            "status": key.status,
            "created_at": key.created_at,
            "last_used_at": key.last_used_at
        })
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login": user.last_login,
        "key_count": len(keys),
        "keys": keys_list
    }

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新用户角色"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    new_role = role_data.get("role")
    if new_role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="无效的角色")
    
    # 不能修改自己的角色
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    
    user.role = new_role
    db.commit()
    
    return {"message": f"用户角色已更新为 {new_role}", "success": True}

@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """启用/禁用用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能禁用自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己的账户")
    
    is_active = status_data.get("is_active", True)
    user.is_active = is_active
    db.commit()
    
    status_text = "启用" if is_active else "禁用"
    return {"message": f"用户已{status_text}", "success": True}


# ============ 服务商管理 ============

@router.get("/providers")
def get_providers_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取所有服务商（管理员视图）"""
    providers = db.query(ApiProvider).order_by(ApiProvider.sort_order).all()
    
    result = []
    for p in providers:
        model_count = db.query(ApiModel).filter(ApiModel.provider_id == p.id).count()
        key_count = db.query(UserApiKey).filter(UserApiKey.provider_id == p.id).count()
        result.append({
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "base_url": p.base_url,
            "description": p.description,
            "icon": p.icon,
            "is_active": p.is_active,
            "is_custom": p.is_custom,
            "created_by": p.created_by,
            "sort_order": p.sort_order,
            "created_at": p.created_at,
            "model_count": model_count,
            "key_count": key_count
        })
    
    return result

@router.post("/providers")
def create_provider_admin(
    provider_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """管理员创建全局服务商（所有用户可见）"""
    
    # 检查 name 是否重复
    if db.query(ApiProvider).filter(ApiProvider.name == provider_data.get("name")).first():
        raise HTTPException(status_code=400, detail="服务商标识已存在")
    
    # 检查 display_name 是否重复
    if db.query(ApiProvider).filter(ApiProvider.display_name == provider_data.get("display_name")).first():
        raise HTTPException(status_code=400, detail="服务商名称已存在")
    
    # 获取最大排序号
    max_order = db.query(ApiProvider).count()
    
    new_provider = ApiProvider(
        name=provider_data.get("name"),
        display_name=provider_data.get("display_name"),
        base_url=provider_data.get("base_url"),
        description=provider_data.get("description"),
        icon=provider_data.get("icon", "link"),
        is_active=True,
        is_custom=False,  # 管理员创建的是全局服务商
        created_by=None,  # 全局服务商不需要创建者
        sort_order=provider_data.get("sort_order", max_order + 1)
    )
    
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    
    return {
        "message": "服务商创建成功",
        "id": new_provider.id,
        "success": True
    }

@router.put("/providers/{provider_id}/status")
def update_provider_status(
    provider_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """启用/禁用服务商"""
    provider = db.query(ApiProvider).filter(ApiProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="服务商不存在")
    
    is_active = status_data.get("is_active", True)
    provider.is_active = is_active
    db.commit()
    
    status_text = "启用" if is_active else "禁用"
    return {"message": f"服务商已{status_text}", "success": True}

@router.put("/providers/{provider_id}")
def update_provider(
    provider_id: int,
    provider_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新服务商信息"""
    provider = db.query(ApiProvider).filter(ApiProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="服务商不存在")
    
    if "display_name" in provider_data:
        provider.display_name = provider_data["display_name"]
    if "base_url" in provider_data:
        provider.base_url = provider_data["base_url"]
    if "description" in provider_data:
        provider.description = provider_data["description"]
    if "icon" in provider_data:
        provider.icon = provider_data["icon"]
    if "sort_order" in provider_data:
        provider.sort_order = provider_data["sort_order"]
    
    db.commit()
    db.refresh(provider)
    
    return {"message": "服务商信息已更新", "success": True}


# ============ 模型管理 ============

@router.get("/models")
def get_models_admin(
    provider_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取所有模型（管理员视图）"""
    query = db.query(ApiModel)
    
    if provider_id:
        query = query.filter(ApiModel.provider_id == provider_id)
    
    models = query.order_by(ApiModel.provider_id, ApiModel.sort_order).all()
    
    result = []
    for m in models:
        provider = db.query(ApiProvider).filter(ApiProvider.id == m.provider_id).first()
        result.append({
            "id": m.id,
            "provider_id": m.provider_id,
            "provider_name": provider.display_name if provider else "未知",
            "model_id": m.model_id,
            "model_name": m.model_name,
            "category": m.category,
            "context_window": m.context_window,
            "is_default": m.is_default,
            "sort_order": m.sort_order
        })
    
    return result

@router.post("/models")
def create_model(
    model_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """添加新模型"""
    provider = db.query(ApiProvider).filter(ApiProvider.id == model_data.get("provider_id")).first()
    if not provider:
        raise HTTPException(status_code=404, detail="服务商不存在")
    
    # 检查模型ID是否已存在
    existing = db.query(ApiModel).filter(
        ApiModel.provider_id == model_data["provider_id"],
        ApiModel.model_id == model_data["model_id"]
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该模型ID已存在")
    
    new_model = ApiModel(
        provider_id=model_data["provider_id"],
        model_id=model_data["model_id"],
        model_name=model_data.get("model_name", model_data["model_id"]),
        category=model_data.get("category", "chat"),
        context_window=model_data.get("context_window"),
        is_default=model_data.get("is_default", False),
        sort_order=model_data.get("sort_order", 0)
    )
    
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return {"message": "模型添加成功", "id": new_model.id, "success": True}

@router.put("/models/{model_id}")
def update_model(
    model_id: int,
    model_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新模型信息"""
    model = db.query(ApiModel).filter(ApiModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    if "model_name" in model_data:
        model.model_name = model_data["model_name"]
    if "category" in model_data:
        model.category = model_data["category"]
    if "context_window" in model_data:
        model.context_window = model_data["context_window"]
    if "is_default" in model_data:
        model.is_default = model_data["is_default"]
    if "sort_order" in model_data:
        model.sort_order = model_data["sort_order"]
    
    db.commit()
    
    return {"message": "模型信息已更新", "success": True}

@router.delete("/models/{model_id}")
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除模型"""
    model = db.query(ApiModel).filter(ApiModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    db.delete(model)
    db.commit()
    
    return {"message": "模型已删除", "success": True}

# Provider name to ID mapping
PROVIDER_NAME_MAP = {
    "openai": 1,
    "anthropic": 2,
    "google": 3,
    "azure": 4,
    "deepseek": 5,
    "moonshot": 6,
    "zhipu": 7,
    "baidu": 8,
    "alibaba": 9,
    "custom": 10
}

@router.get("/config/status")
def get_config_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get current model configuration status"""
    total_models = db.query(ApiModel).count()
    total_providers = db.query(ApiProvider).filter(ApiProvider.is_active == True).count()
    
    return {
        "total_models": total_models,
        "total_providers": total_providers,
        "remote_url": settings.MODEL_CONFIG_URL or "Not configured",
        "local_config": settings.MODEL_CONFIG_LOCAL_PATH
    }

@router.post("/config/sync", response_model=MessageResponse)
async def sync_model_config(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    source: Optional[str] = None  # "remote" or "local"
):
    """Sync model configuration from remote URL or local file"""
    
    config_data = None
    
    if source == "remote" or (source is None and settings.MODEL_CONFIG_URL):
        # Try remote first
        if not settings.MODEL_CONFIG_URL:
            raise HTTPException(status_code=400, detail="Remote URL not configured")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(settings.MODEL_CONFIG_URL)
                response.raise_for_status()
                config_data = response.json()
        except Exception as e:
            if source == "remote":
                raise HTTPException(status_code=500, detail=f"Failed to fetch remote config: {str(e)}")
            # Fall back to local if remote fails
    
    if config_data is None:
        # Use local config file
        try:
            with open(settings.MODEL_CONFIG_LOCAL_PATH, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Local config file not found")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON in local config file")
    
    # Update database with config
    updated_count = 0
    added_count = 0
    
    models_config = config_data.get("models", {})
    
    for provider_name, models in models_config.items():
        provider_id = PROVIDER_NAME_MAP.get(provider_name)
        if not provider_id:
            continue
        
        for model_data in models:
            model_id = model_data.get("model_id")
            if not model_id:
                continue
            
            # Check if model exists
            existing = db.query(ApiModel).filter(
                ApiModel.provider_id == provider_id,
                ApiModel.model_id == model_id
            ).first()
            
            if existing:
                # Update existing model
                existing.model_name = model_data.get("model_name", model_id)
                existing.category = model_data.get("category", "chat")
                existing.context_window = model_data.get("context_window")
                existing.is_default = model_data.get("is_default", False)
                updated_count += 1
            else:
                # Add new model
                new_model = ApiModel(
                    provider_id=provider_id,
                    model_id=model_id,
                    model_name=model_data.get("model_name", model_id),
                    category=model_data.get("category", "chat"),
                    context_window=model_data.get("context_window"),
                    is_default=model_data.get("is_default", False),
                    sort_order=model_data.get("sort_order", 0)
                )
                db.add(new_model)
                added_count += 1
    
    db.commit()
    
    return MessageResponse(
        message=f"Config synced: {added_count} models added, {updated_count} models updated",
        success=True
    )

@router.post("/config/upload", response_model=MessageResponse)
async def upload_model_config(
    config_json: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Upload and apply model configuration directly"""
    
    updated_count = 0
    added_count = 0
    
    models_config = config_json.get("models", {})
    
    for provider_name, models in models_config.items():
        provider_id = PROVIDER_NAME_MAP.get(provider_name)
        if not provider_id:
            continue
        
        for model_data in models:
            model_id = model_data.get("model_id")
            if not model_id:
                continue
            
            existing = db.query(ApiModel).filter(
                ApiModel.provider_id == provider_id,
                ApiModel.model_id == model_id
            ).first()
            
            if existing:
                existing.model_name = model_data.get("model_name", model_id)
                existing.category = model_data.get("category", "chat")
                existing.context_window = model_data.get("context_window")
                existing.is_default = model_data.get("is_default", False)
                updated_count += 1
            else:
                new_model = ApiModel(
                    provider_id=provider_id,
                    model_id=model_id,
                    model_name=model_data.get("model_name", model_id),
                    category=model_data.get("category", "chat"),
                    context_window=model_data.get("context_window"),
                    is_default=model_data.get("is_default", False),
                    sort_order=model_data.get("sort_order", 0)
                )
                db.add(new_model)
                added_count += 1
    
    db.commit()
    
    return MessageResponse(
        message=f"Config applied: {added_count} models added, {updated_count} models updated",
        success=True
    )
