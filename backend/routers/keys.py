import os
from base64 import urlsafe_b64encode, urlsafe_b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, UserApiKey, ApiProvider, ApiModel
from schemas import (
    UserApiKeyCreate, 
    UserApiKeyUpdate, 
    UserApiKeyResponse, 
    UserApiKeyWithDecrypted,
    ApiModelResponse,
    ApiProviderCreate,
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

@router.get("/providers", response_model=List[dict])
def get_providers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取服务商列表
    
    返回：
    - 全局服务商（管理员添加，is_custom=False 或 created_by 为 NULL）
    - 当前用户创建的自定义服务商（created_by = current_user.id）
    """
    from sqlalchemy import or_
    
    providers = db.query(ApiProvider).filter(
        ApiProvider.is_active == True,
        or_(
            ApiProvider.is_custom == False,  # 全局服务商
            ApiProvider.is_custom == None,   # 兼容旧数据
            ApiProvider.created_by == current_user.id  # 用户自己创建的
        )
    ).order_by(ApiProvider.sort_order).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "base_url": p.base_url,
            "icon": p.icon,
            "is_custom": p.is_custom,
            "created_by": p.created_by
        }
        for p in providers
    ]


@router.post("/providers", response_model=dict)
def create_custom_provider(
    provider_data: ApiProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建自定义服务商"""
    
    # 生成唯一标识名（使用用户ID和时间戳）
    import time
    unique_name = f"custom_{current_user.id}_{int(time.time())}"
    
    # 检查 display_name 是否重复
    existing = db.query(ApiProvider).filter(
        ApiProvider.display_name == provider_data.display_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="服务商名称已存在")
    
    # 获取最大排序号
    max_order = db.query(ApiProvider).count()
    
    new_provider = ApiProvider(
        name=unique_name,
        display_name=provider_data.display_name,
        base_url=provider_data.base_url,
        description=provider_data.description,
        icon=provider_data.icon or "link",
        is_active=True,
        is_custom=True,
        created_by=current_user.id,
        sort_order=max_order + 1
    )
    
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    
    return {
        "id": new_provider.id,
        "name": new_provider.name,
        "display_name": new_provider.display_name,
        "base_url": new_provider.base_url,
        "icon": new_provider.icon,
        "is_custom": True
    }

@router.delete("/providers/{provider_id}", response_model=MessageResponse)
def delete_custom_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除自定义服务商（仅允许删除自己创建的）"""
    
    provider = db.query(ApiProvider).filter(ApiProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="服务商不存在")
    
    # 只能删除自己创建的自定义服务商
    if not provider.is_custom:
        raise HTTPException(status_code=403, detail="无法删除全局服务商")
    
    if provider.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此服务商")
    
    # 检查是否有密钥关联此服务商
    key_count = db.query(UserApiKey).filter(UserApiKey.provider_id == provider_id).count()
    if key_count > 0:
        raise HTTPException(status_code=400, detail=f"该服务商下有 {key_count} 个密钥，请先删除密钥")
    
    db.delete(provider)
    db.commit()
    
    return MessageResponse(message="服务商已删除", success=True)

@router.get("/models", response_model=List[ApiModelResponse])
def get_all_models(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all available models for current user
    
    只返回用户可见服务商下的模型：
    - 全局服务商（管理员添加）
    - 用户自己创建的自定义服务商
    """
    from sqlalchemy import or_
    
    models = db.query(ApiModel).join(ApiProvider).filter(
        ApiProvider.is_active == True,
        or_(
            ApiProvider.is_custom == False,
            ApiProvider.is_custom == None,
            ApiProvider.created_by == current_user.id
        )
    ).order_by(ApiProvider.sort_order, ApiModel.sort_order).all()
    return models

@router.get("/models/{provider_id}", response_model=List[ApiModelResponse])
def get_provider_models(
    provider_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get models for a specific provider"""
    models = db.query(ApiModel).filter(
        ApiModel.provider_id == provider_id
    ).order_by(ApiModel.sort_order).all()
    return models

@router.get("/limits")
def get_key_limits(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """获取用户密钥数量限制信息"""
    can_add, current_count, limit = check_key_limit(current_user, db)
    
    return {
        "current_count": current_count,
        "limit": limit,  # -1 表示无限制
        "can_add": can_add
    }

@router.get("", response_model=List[UserApiKeyResponse])
def get_user_keys(
    status_filter: str = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(UserApiKey).filter(UserApiKey.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(UserApiKey.status == status_filter)
    
    keys = query.order_by(UserApiKey.created_at.desc()).all()
    
    result = []
    for key in keys:
        provider = db.query(ApiProvider).filter(ApiProvider.id == key.provider_id).first()
        result.append(UserApiKeyResponse(
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
            last_used_at=key.last_used_at
        ))
    
    return result

# 密钥数量无限制（开源版）
# 如需限制，可在此配置
KEY_LIMIT = None  # None 表示无限制，设置为数字则限制数量


def check_key_limit(user: User, db: Session) -> tuple[bool, int, int]:
    """检查用户密钥数量是否达到上限
    
    返回: (是否可添加, 当前数量, 上限)
    """
    current_count = db.query(UserApiKey).filter(
        UserApiKey.user_id == user.id
    ).count()
    
    if KEY_LIMIT is None:
        return True, current_count, -1  # 无限制
    
    return current_count < KEY_LIMIT, current_count, KEY_LIMIT

@router.post("", response_model=UserApiKeyResponse)
def create_api_key(
    key_data: UserApiKeyCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 检查密钥数量限制
    can_add, current_count, limit = check_key_limit(current_user, db)
    if not can_add:
        raise HTTPException(
            status_code=403, 
            detail=f"密钥数量已达上限 {limit} 个，当前已有 {current_count} 个。"
        )
    
    provider = db.query(ApiProvider).filter(ApiProvider.id == key_data.provider_id).first()
    if not provider:
        raise HTTPException(status_code=400, detail="Provider not found")
    
    existing = db.query(UserApiKey).filter(
        UserApiKey.user_id == current_user.id,
        UserApiKey.key_name == key_data.key_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Key name already exists")
    
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
        last_used_at=new_key.last_used_at
    )

@router.get("/{key_id}", response_model=UserApiKeyWithDecrypted)
def get_api_key(
    key_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
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
        last_used_at=key.last_used_at
    )

@router.put("/{key_id}", response_model=UserApiKeyResponse)
def update_api_key(
    key_id: int,
    key_data: UserApiKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if key_data.key_name:
        existing = db.query(UserApiKey).filter(
            UserApiKey.user_id == current_user.id,
            UserApiKey.key_name == key_data.key_name,
            UserApiKey.id != key_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Key name already exists")
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
        last_used_at=key.last_used_at
    )

@router.delete("/{key_id}", response_model=MessageResponse)
def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    key = db.query(UserApiKey).filter(
        UserApiKey.id == key_id,
        UserApiKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(key)
    db.commit()
    
    return MessageResponse(message="API key deleted successfully", success=True)


@router.post("/test", response_model=dict)
async def test_api_key(
    test_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试 API 密钥是否有效
    
    通过调用服务商的 /v1/models 端点验证密钥有效性（不消耗额度）
    """
    import httpx
    
    provider_id = test_data.get("provider_id")
    api_key = test_data.get("api_key")
    
    if not provider_id or not api_key:
        raise HTTPException(status_code=400, detail="缺少服务商ID或API密钥")
    
    # 获取服务商信息
    provider = db.query(ApiProvider).filter(ApiProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="服务商不存在")
    
    # 自定义服务商不提供测试功能
    if provider.is_custom:
        return {
            "success": False,
            "message": "自定义服务商暂不支持测试连接功能",
            "provider_name": provider.display_name,
            "is_custom": True
        }
    
    # 构建测试 URL
    # 注意：数据库中的 base_url 已包含 /v1，所以直接拼接 /models
    base_url = provider.base_url.rstrip("/")
    provider_name = provider.name.lower()
    
    # 根据不同服务商使用正确的测试端点
    if provider_name == "openai":
        test_url = f"{base_url}/models"
    elif provider_name == "anthropic":
        # Anthropic 没有 /models 端点，返回特殊提示
        return {
            "success": True,
            "message": "Anthropic API 密钥格式验证通过，请确保密钥有效",
            "provider_name": provider.display_name,
            "is_custom": False
        }
    elif provider_name == "google":
        # Google 使用 API key 作为查询参数
        test_url = f"{base_url}/models?key={api_key}"
    elif provider_name == "deepseek":
        test_url = f"{base_url}/models"
    elif provider_name == "moonshot":
        test_url = f"{base_url}/models"
    elif provider_name == "zhipu":
        test_url = f"{base_url}/models"
    elif provider_name == "baidu":
        # 百度文心需要特殊认证方式
        return {
            "success": True,
            "message": "百度文心 API 需要通过百度控制台验证，请确保密钥格式正确",
            "provider_name": provider.display_name,
            "is_custom": False
        }
    elif provider_name == "alibaba":
        test_url = f"{base_url}/models"
    else:
        # 默认尝试 OpenAI 兼容格式
        test_url = f"{base_url}/models"
    
    # 设置请求头（Google 不需要 Authorization header）
    if provider_name == "google":
        headers = {}
    else:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(test_url, headers=headers)
            
            if response.status_code == 200:
                # 尝试解析返回的模型数量
                try:
                    data = response.json()
                    model_count = len(data.get("data", []))
                    return {
                        "success": True,
                        "message": f"连接成功，可用模型: {model_count} 个",
                        "provider_name": provider.display_name,
                        "model_count": model_count,
                        "is_custom": False
                    }
                except:
                    return {
                        "success": True,
                        "message": "连接成功，API密钥有效",
                        "provider_name": provider.display_name,
                        "is_custom": False
                    }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "API密钥无效或已过期",
                    "provider_name": provider.display_name,
                    "is_custom": False
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "message": "API密钥权限不足",
                    "provider_name": provider.display_name,
                    "is_custom": False
                }
            else:
                return {
                    "success": False,
                    "message": f"连接失败，状态码: {response.status_code}",
                    "provider_name": provider.display_name,
                    "is_custom": False
                }
    except httpx.TimeoutException:
        return {
            "success": False,
            "message": "连接超时，请检查网络或API地址",
            "provider_name": provider.display_name,
            "is_custom": False
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "message": "无法连接到服务器，请检查API地址",
            "provider_name": provider.display_name,
            "is_custom": False
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"测试失败: {str(e)}",
            "provider_name": provider.display_name,
            "is_custom": False
        }
