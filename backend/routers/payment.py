# -*- coding: utf-8 -*-
"""
爱发电支付回调处理
文档：https://afdian.net/p/dev
"""
import os
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import json
import logging

from database import get_db
from models import User
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/webhook", tags=["payment"])
logger = logging.getLogger(__name__)

# 爱发电配置（从环境变量读取）
AFDIAN_TOKEN = os.getenv("AFDIAN_TOKEN", "")
AFDIAN_USER_ID = os.getenv("AFDIAN_USER_ID", "")

# 检查配置
if settings.ENV == "production" and not AFDIAN_TOKEN:
    logger.warning("生产环境未配置 AFDIAN_TOKEN，支付回调将无法验证签名！")

# 订阅方案映射
PLAN_MAP = {
    # 基础版月付
    "basic_monthly": {"tier": "basic", "days": 30},
    # 基础版年付
    "basic_yearly": {"tier": "basic", "days": 365},
    # 专业版月付
    "pro_monthly": {"tier": "pro", "days": 30},
    # 专业版年付
    "pro_yearly": {"tier": "pro", "days": 365},
}


def verify_afdian_signature(data: dict, token: str) -> bool:
    """
    验证爱发电回调签名
    
    爱发电签名规则：
    1. 将 params 按 key 字母排序
    2. 拼接成 key1=value1&key2=value2 格式
    3. 在末尾拼接 token
    4. 计算 MD5
    """
    try:
        params = data.get("params", {})
        if not params:
            return False
            
        # 按 key 排序并拼接
        sorted_keys = sorted(params.keys())
        sign_str = "&".join([f"{k}={params[k]}" for k in sorted_keys])
        sign_str += token
        
        # 计算 MD5
        calculated_sign = hashlib.md5(sign_str.encode()).hexdigest()
        received_sign = data.get("sign", "")
        
        return calculated_sign == received_sign
    except Exception as e:
        logger.error(f"签名验证失败: {e}")
        return False


@router.post("/afdian")
async def afdian_webhook(request: Request, db: Session = Depends(get_db)):
    """
    接收爱发电支付回调
    
    爱发电回调数据格式：
    {
        "ec": 200,
        "em": "success",
        "data": {
            "type": "order",  # order=订单, sponsorship=赞助
            "order": {
                "out_trade_no": "xxx",  # 平台订单号
                "user_id": "xxx",       # 爱发电用户ID
                "plan_id": "xxx",       # 方案ID
                "month": 1,             # 购买月数
                "total_amount": "19.00", # 支付金额
                "show_amount": "19.00",  # 显示金额
                "status": 2,             # 2=已支付
                "remark": "custom参数",   # 用户自定义参数（我们传的user_id）
                "product_type": 0,       # 0=赞助方案
                "discount": "0.00",
                "sku_id": "",
                "create_time": 1234567890,
                "pay_time": 1234567890
            }
        }
    }
    """
    try:
        data = await request.json()
        logger.info(f"收到爱发电回调: {json.dumps(data, ensure_ascii=False)}")
        
        # 签名验证（生产环境强制验证，开发环境可选跳过）
        if settings.ENV == "production":
            if not AFDIAN_TOKEN:
                logger.error("生产环境未配置 AFDIAN_TOKEN")
                raise HTTPException(status_code=500, detail="Server configuration error")
            if not verify_afdian_signature(data, AFDIAN_TOKEN):
                logger.warning("签名验证失败")
                raise HTTPException(status_code=400, detail="Invalid signature")
        else:
            # 开发环境：如果配置了 token 则验证，否则跳过
            if AFDIAN_TOKEN and not verify_afdian_signature(data, AFDIAN_TOKEN):
                logger.warning("签名验证失败（开发环境）")
                raise HTTPException(status_code=400, detail="Invalid signature")
            logger.debug("开发环境跳过签名验证")
        
        # 检查响应状态
        if data.get("ec") != 200:
            logger.error(f"爱发电回调错误: {data.get('em')}")
            return {"status": "error", "message": data.get("em")}
        
        order_data = data.get("data", {}).get("order", {})
        
        if not order_data:
            return {"status": "ignored", "message": "No order data"}
        
        # 只处理已支付的订单
        if order_data.get("status") != 2:
            return {"status": "ignored", "message": "Order not paid"}
        
        # 获取用户ID（通过remark/custom参数传递）
        custom_data = order_data.get("remark", "")
        
        # 解析用户ID（格式：user_123 或直接是数字ID）
        try:
            if custom_data.startswith("user_"):
                user_id = int(custom_data.replace("user_", ""))
            else:
                user_id = int(custom_data)
        except (ValueError, TypeError):
            logger.error(f"无法解析用户ID: {custom_data}")
            return {"status": "error", "message": "Invalid user id"}
        
        # 获取方案信息
        plan_id = order_data.get("plan_id", "")
        months = order_data.get("month", 1)
        
        # 确定会员等级
        # 根据金额判断是基础版还是专业版
        total_amount = float(order_data.get("total_amount", 0))
        
        if total_amount >= 49:  # 专业版
            tier = "pro"
        elif total_amount >= 19:  # 基础版
            tier = "basic"
        else:
            logger.warning(f"金额不足以开通会员: {total_amount}")
            return {"status": "ignored", "message": "Amount too low"}
        
        # 计算会员天数
        days = months * 30
        
        # 更新用户会员状态
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"用户不存在: {user_id}")
            return {"status": "error", "message": "User not found"}
        
        # 计算到期时间
        now = datetime.utcnow()
        if user.membership_expire_at and user.membership_expire_at > now:
            # 如果已有会员且未过期，在现有基础上延长
            new_expire = user.membership_expire_at + timedelta(days=days)
        else:
            # 新开通或已过期，从现在开始计算
            new_expire = now + timedelta(days=days)
        
        # 更新会员信息
        user.membership_tier = tier
        user.membership_expire_at = new_expire
        if not user.membership_started_at:
            user.membership_started_at = now
        
        db.commit()
        
        logger.info(f"用户 {user_id} 开通 {tier} 会员成功，到期时间: {new_expire}")
        
        return {
            "status": "ok",
            "message": f"Membership updated: {tier} until {new_expire.strftime('%Y-%m-%d')}"
        }
        
    except json.JSONDecodeError:
        logger.error("无效的JSON数据")
        return {"status": "error", "message": "Invalid JSON"}
    except Exception as e:
        logger.error(f"处理回调失败: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/membership/status")
async def get_membership_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户会员状态
    """
    now = datetime.utcnow()
    is_active = False
    days_left = 0
    
    if current_user.membership_expire_at and current_user.membership_expire_at > now:
        is_active = True
        days_left = (current_user.membership_expire_at - now).days
    
    return {
        "tier": current_user.membership_tier or "free",
        "is_active": is_active,
        "expire_at": current_user.membership_expire_at.isoformat() if current_user.membership_expire_at else None,
        "days_left": days_left,
        "started_at": current_user.membership_started_at.isoformat() if current_user.membership_started_at else None
    }
