import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import ApiProvider, ApiModel
from schemas import MessageResponse
from auth import get_current_admin_user
from models import User
from config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

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
