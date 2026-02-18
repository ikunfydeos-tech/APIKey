# -*- coding: utf-8 -*-
"""
会员服务模块
- 会员到期检查
- 到期提醒
- 自动降级
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import SessionLocal
from models import User, LogEntry

logger = logging.getLogger(__name__)

# 提醒配置
REMINDER_DAYS = [7, 3, 1]  # 提前7天、3天、1天提醒

# 初始化定时任务调度器
scheduler = AsyncIOScheduler()


def get_membership_service():
    """获取会员服务实例"""
    return MembershipService()


class MembershipService:
    """会员服务类"""
    
    def check_expiring_memberships(self, db: Session) -> List[dict]:
        """
        检查即将到期的会员
        返回需要发送提醒的用户列表
        """
        now = datetime.utcnow()
        results = []
        
        for days in REMINDER_DAYS:
            # 计算目标日期范围
            target_start = now + timedelta(days=days)
            target_end = target_start + timedelta(hours=24)
            
            # 查询在该日期范围内到期的付费用户
            users = db.query(User).filter(
                User.membership_tier.in_(['basic', 'pro']),
                User.membership_expire_at >= target_start,
                User.membership_expire_at < target_end,
                User.is_active == True
            ).all()
            
            for user in users:
                results.append({
                    'user': user,
                    'days_left': days,
                    'expire_at': user.membership_expire_at
                })
        
        return results
    
    def check_expired_memberships(self, db: Session) -> List[User]:
        """
        检查已过期的会员
        返回需要降级的用户列表
        """
        now = datetime.utcnow()
        
        # 查询已过期但仍标记为付费的用户
        expired_users = db.query(User).filter(
            User.membership_tier.in_(['basic', 'pro']),
            User.membership_expire_at < now,
            User.is_active == True
        ).all()
        
        return expired_users
    
    def downgrade_membership(self, db: Session, user: User) -> bool:
        """
        将用户会员降级为免费版
        """
        try:
            old_tier = user.membership_tier
            
            user.membership_tier = 'free'
            # 保留到期时间记录，便于续费后恢复
            
            db.commit()
            
            # 记录日志
            log = LogEntry(
                user_id=user.id,
                username=user.username,
                action='membership_expired',
                resource_type='USER',
                resource_id=user.id,
                resource_name=user.username,
                status='success',
                details=f'会员从 {old_tier} 降级为 free'
            )
            db.add(log)
            db.commit()
            
            logger.info(f"用户 {user.username} 会员已过期，从 {old_tier} 降级为 free")
            return True
            
        except Exception as e:
            logger.error(f"降级用户 {user.username} 会员失败: {e}")
            db.rollback()
            return False
    
    def send_expiry_reminder(self, db: Session, user: User, days_left: int) -> bool:
        """
        发送到期提醒
        TODO: 接入邮件服务
        """
        try:
            # 记录提醒日志
            log = LogEntry(
                user_id=user.id,
                username=user.username,
                action='membership_reminder',
                resource_type='USER',
                resource_id=user.id,
                resource_name=user.username,
                status='success',
                details=f'会员将于 {days_left} 天后到期'
            )
            db.add(log)
            db.commit()
            
            logger.info(f"已发送到期提醒给用户 {user.username}，剩余 {days_left} 天")
            
            # TODO: 发送邮件提醒
            # self._send_email(user.email, days_left, user.membership_expire_at)
            
            return True
            
        except Exception as e:
            logger.error(f"发送提醒给用户 {user.username} 失败: {e}")
            return False
    
    def _send_email(self, email: str, days_left: int, expire_at: datetime):
        """
        发送邮件提醒
        TODO: 实现邮件发送
        """
        # 邮件内容模板
        subject = f"您的会员将于{days_left}天后到期"
        body = f"""
您好，

您的API密钥管家会员将于 {expire_at.strftime('%Y-%m-%d')} 到期。

到期后，您的账户将自动降级为免费版：
- 密钥数量限制为5个
- 部分高级功能将无法使用

如需继续使用高级功能，请及时续费。

感谢您的支持！
API密钥管家团队
        """
        # TODO: 调用邮件服务发送
        pass


async def check_memberships_job():
    """
    定时任务：检查会员状态
    每天凌晨2点执行
    """
    logger.info("开始执行会员状态检查任务...")
    
    db = SessionLocal()
    try:
        service = MembershipService()
        
        # 1. 检查即将到期的会员，发送提醒
        expiring = service.check_expiring_memberships(db)
        for item in expiring:
            service.send_expiry_reminder(
                db, 
                item['user'], 
                item['days_left']
            )
        
        logger.info(f"已发送 {len(expiring)} 条到期提醒")
        
        # 2. 检查已过期的会员，执行降级
        expired = service.check_expired_memberships(db)
        for user in expired:
            service.downgrade_membership(db, user)
        
        logger.info(f"已降级 {len(expired)} 个过期会员")
        
    except Exception as e:
        logger.error(f"会员状态检查任务失败: {e}")
    finally:
        db.close()


async def check_membership_on_login(user_id: int, db: Session) -> dict:
    """
    用户登录时检查会员状态
    返回会员信息和提醒
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {'tier': 'free', 'is_active': False}
    
    now = datetime.utcnow()
    
    # 检查是否已过期
    if user.membership_tier != 'free' and user.membership_expire_at:
        if user.membership_expire_at < now:
            # 已过期，执行降级
            service = MembershipService()
            service.downgrade_membership(db, user)
            
            return {
                'tier': 'free',
                'is_active': False,
                'expired': True,
                'message': '您的会员已过期，已自动降级为免费版'
            }
        
        # 计算剩余天数
        days_left = (user.membership_expire_at - now).days
        
        return {
            'tier': user.membership_tier,
            'is_active': True,
            'expire_at': user.membership_expire_at.isoformat(),
            'days_left': days_left,
            'reminder': days_left in REMINDER_DAYS
        }
    
    return {
        'tier': user.membership_tier or 'free',
        'is_active': user.membership_tier != 'free'
    }


def check_membership_on_login_sync(user_id: int, db: Session) -> dict:
    """
    用户登录时检查会员状态（同步版本）
    返回会员信息和提醒
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {'tier': 'free', 'is_active': False}
    
    now = datetime.utcnow()
    
    # 检查是否已过期
    if user.membership_tier != 'free' and user.membership_expire_at:
        if user.membership_expire_at < now:
            # 已过期，执行降级
            service = MembershipService()
            service.downgrade_membership(db, user)
            
            return {
                'tier': 'free',
                'is_active': False,
                'expired': True,
                'message': '您的会员已过期，已自动降级为免费版'
            }
        
        # 计算剩余天数
        days_left = (user.membership_expire_at - now).days
        
        return {
            'tier': user.membership_tier,
            'is_active': True,
            'expire_at': user.membership_expire_at.isoformat(),
            'days_left': days_left,
            'reminder': days_left in REMINDER_DAYS
        }
    
    return {
        'tier': user.membership_tier or 'free',
        'is_active': user.membership_tier != 'free'
    }


def start_scheduler():
    """启动定时任务调度器"""
    # 每天凌晨2点执行会员检查
    scheduler.add_job(
        check_memberships_job,
        CronTrigger(hour=2, minute=0),
        id='membership_check',
        replace_existing=True
    )
    
    # 每小时检查一次（用于测试）
    # scheduler.add_job(
    #     check_memberships_job,
    #     CronTrigger(minute=0),
    #     id='membership_check_hourly',
    #     replace_existing=True
    # )
    
    scheduler.start()
    logger.info("会员检查定时任务已启动")


def stop_scheduler():
    """停止定时任务调度器"""
    scheduler.shutdown()
    logger.info("会员检查定时任务已停止")
