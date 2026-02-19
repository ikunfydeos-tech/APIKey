#!/usr/bin/env python3
"""
API密钥管理系统重构测试脚本
用于验证重构后的系统功能
"""

import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

from sqlalchemy import create_engine, text
from config import settings
from models import User, UserBalance, APIUsageLog, SubscriptionRenewal
from database import SessionLocal

def test_database_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("测试数据库连接...")
    print("=" * 50)
    
    try:
        if settings.USE_SQLITE:
            engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_database_tables():
    """测试数据库表结构"""
    print("=" * 50)
    print("测试数据库表结构...")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        
        # 检查表是否存在
        tables_to_check = [
            "users",
            "user_balances", 
            "api_usage_logs",
            "subscription_renewals",
            "balance_change_logs",
            "ip_location_records"
        ]
        
        for table_name in tables_to_check:
            try:
                result = db.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
                if result.fetchone():
                    print(f"✅ 表 '{table_name}' 存在")
                else:
                    print(f"❌ 表 '{table_name}' 不存在")
                    return False
            except Exception as e:
                print(f"❌ 检查表 '{table_name}' 失败: {e}")
                return False
        
        db.close()
        print("✅ 所有表结构验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 表结构测试失败: {e}")
        return False

def test_user_registration():
    """测试用户注册功能"""
    print("=" * 50)
    print("测试用户注册功能...")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        
        # 检查是否已有测试用户
        test_username = "testuser_refactored"
        existing_user = db.query(User).filter(User.username == test_username).first()
        
        if existing_user:
            print(f"✅ 测试用户 '{test_username}' 已存在")
            return True
        
        # 创建测试用户
        from auth import get_password_hash
        
        hashed_password = get_password_hash("test123456")
        new_user = User(
            username=test_username,
            email="test@example.com",
            password_hash=hashed_password,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ 测试用户 '{test_username}' 创建成功")
        
        # 验证用户是否可以查询
        found_user = db.query(User).filter(User.username == test_username).first()
        if found_user:
            print(f"✅ 用户查询成功，ID: {found_user.id}")
            return True
        else:
            print("❌ 用户查询失败")
            return False
            
    except Exception as e:
        print(f"❌ 用户注册测试失败: {e}")
        return False
    finally:
        db.close()

def test_balance_management():
    """测试余额管理功能"""
    print("=" * 50)
    print("测试余额管理功能...")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        
        # 查找测试用户
        test_username = "testuser_refactored"
        user = db.query(User).filter(User.username == test_username).first()
        
        if not user:
            print("❌ 测试用户不存在，无法测试余额功能")
            return False
        
        # 检查用户余额表
        user_balance = db.query(UserBalance).filter(UserBalance.user_id == user.id).first()
        
        if not user_balance:
            # 创建测试余额记录
            from models import ApiProvider
            
            # 获取一个测试提供商
            provider = db.query(ApiProvider).first()
            if not provider:
                print("❌ 没有可用的提供商，无法创建余额记录")
                return False
            
            new_balance = UserBalance(
                user_id=user.id,
                provider_id=provider.id,
                balance=100.0
            )
            db.add(new_balance)
            db.commit()
            db.refresh(new_balance)
            print(f"✅ 创建测试余额记录，余额: {new_balance.balance}")
        else:
            print(f"✅ 用户余额记录已存在，余额: {user_balance.balance}")
        
        # 测试余额查询
        balances = db.query(UserBalance).filter(UserBalance.user_id == user.id).all()
        print(f"✅ 查询到 {len(balances)} 条余额记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 余额管理测试失败: {e}")
        return False
    finally:
        db.close()

def test_api_usage_tracking():
    """测试API使用追踪功能"""
    print("=" * 50)
    print("测试API使用追踪功能...")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        
        # 查找测试用户
        test_username = "testuser_refactored"
        user = db.query(User).filter(User.username == test_username).first()
        
        if not user:
            print("❌ 测试用户不存在，无法测试API使用追踪")
            return False
        
        # 创建测试API使用记录
        from models import ApiProvider, UserApiKey
        
        provider = db.query(ApiProvider).first()
        api_key = db.query(UserApiKey).filter(UserApiKey.user_id == user.id).first()
        
        if not provider:
            print("❌ 没有可用的提供商")
            return False
        
        new_usage_log = APIUsageLog(
            user_id=user.id,
            provider_id=provider.id,
            model_id="test_model",
            tokens_used=100,
            cost=0.01,
            status="success"
        )
        db.add(new_usage_log)
        db.commit()
        db.refresh(new_usage_log)
        
        print(f"✅ 创建测试API使用记录，Token使用: {new_usage_log.tokens_used}")
        
        # 测试查询
        usage_logs = db.query(APIUsageLog).filter(APIUsageLog.user_id == user.id).all()
        print(f"✅ 查询到 {len(usage_logs)} 条API使用记录")
        
        return True
        
    except Exception as e:
        print(f"❌ API使用追踪测试失败: {e}")
        return False
    finally:
        db.close()

def test_subscription_renewal():
    """测试续费功能"""
    print("=" * 50)
    print("测试续费功能...")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        
        # 查找测试用户
        test_username = "testuser_refactored"
        user = db.query(User).filter(User.username == test_username).first()
        
        if not user:
            print("❌ 测试用户不存在，无法测试续费功能")
            return False
        
        # 创建测试续费记录
        new_renewal = SubscriptionRenewal(
            user_id=user.id,
            subscription_type="basic",
            amount=29.99,
            payment_method="test",
            status="pending"
        )
        db.add(new_renewal)
        db.commit()
        db.refresh(new_renewal)
        
        print(f"✅ 创建测试续费记录，状态: {new_renewal.status}")
        
        # 测试查询
        renewals = db.query(SubscriptionRenewal).filter(SubscriptionRenewal.user_id == user.id).all()
        print(f"✅ 查询到 {len(renewals)} 条续费记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 续费功能测试失败: {e}")
        return False
    finally:
        db.close()

def test_totp_functionality():
    """测试TOTP功能"""
    print("=" * 50)
    print("测试TOTP功能...")
    print("=" * 50)
    
    try:
        from totp_utils import generate_totp_secret, enable_totp_for_user, is_totp_enabled
        
        db = SessionLocal()
        
        # 查找测试用户
        test_username = "testuser_refactored"
        user = db.query(User).filter(User.username == test_username).first()
        
        if not user:
            print("❌ 测试用户不存在，无法测试TOTP功能")
            return False
        
        # 检查是否已有TOTP配置
        is_enabled = is_totp_enabled(db, user.id)
        if is_enabled:
            print("✅ TOTP已启用")
        else:
            # 启用TOTP
            secret = generate_totp_secret()
            if enable_totp_for_user(db, user.id, secret):
                print(f"✅ TOTP启用成功，密钥: {secret[:8]}...")
            else:
                print("❌ TOTP启用失败")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ TOTP功能测试失败: {e}")
        return False
    finally:
        db.close()

def main():
    """主测试函数"""
    print("🚀 API密钥管理系统重构测试")
    print("=" * 60)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("数据库表结构", test_database_tables),
        ("用户注册", test_user_registration),
        ("余额管理", test_balance_management),
        ("API使用追踪", test_api_usage_tracking),
        ("续费功能", test_subscription_renewal),
        ("TOTP功能", test_totp_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ 测试 '{test_name}' 失败")
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 异常: {e}")
        print()
    
    print("=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统重构成功。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查系统。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)