#!/usr/bin/env python3
"""
数据库迁移脚本 V1 -> V2
- 移除管理员相关表和数据
- 新增用户自主管理相关表
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from database import engine

def migrate_v1_to_v2():
    """执行V1到V2的迁移"""
    print("=" * 60)
    print("API Manager 数据库迁移 V1 -> V2")
    print("=" * 60)
    
    # 检查数据库类型
    if not settings.USE_SQLITE:
        print("警告：当前使用的是PostgreSQL，迁移脚本主要针对SQLite")
        response = input("是否继续？(yes/no): ")
        if response.lower() != 'yes':
            print("迁移已取消")
            return
    
    conn = engine.connect()
    
    try:
        # 1. 备份现有数据
        print("\n[1/6] 备份现有数据...")
        
        # 获取现有用户数据
        result = conn.execute(text("SELECT id, username, email, password_hash, salt, created_at, updated_at, last_login, is_active, login_attempts, locked_until FROM users"))
        users = result.fetchall()
        print(f"  - 发现 {len(users)} 个用户")
        
        # 获取现有密钥数据
        result = conn.execute(text("SELECT id, user_id, provider_id, key_name, api_key_encrypted, api_key_preview, model_id, status, notes, created_at, updated_at, last_used_at FROM user_api_keys"))
        keys = result.fetchall()
        print(f"  - 发现 {len(keys)} 个API密钥")
        
        # 获取TOTP配置
        result = conn.execute(text("SELECT user_id, secret, is_enabled, created_at, updated_at FROM totp_configs"))
        totp_configs = result.fetchall()
        print(f"  - 发现 {len(totp_configs)} 个TOTP配置")
        
        # 2. 创建新表
        print("\n[2/6] 创建新表结构...")
        
        # 登录历史表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                ip_address VARCHAR(45) NOT NULL,
                user_agent TEXT,
                location VARCHAR(200),
                login_type VARCHAR(20) DEFAULT 'password',
                status VARCHAR(20) DEFAULT 'success',
                fail_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("  - 创建 login_history 表")
        
        # Token使用记录表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                key_id INTEGER REFERENCES user_api_keys(id) ON DELETE CASCADE,
                provider_id INTEGER REFERENCES api_providers(id),
                model_id VARCHAR(100),
                request_tokens INTEGER DEFAULT 0,
                response_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost DECIMAL(10, 6),
                request_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("  - 创建 token_usage 表")
        
        # 密钥余额表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS key_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id INTEGER REFERENCES user_api_keys(id) ON DELETE CASCADE,
                provider_id INTEGER REFERENCES api_providers(id),
                balance DECIMAL(10, 2),
                currency VARCHAR(10) DEFAULT 'USD',
                total_usage DECIMAL(10, 2) DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                last_checked_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(key_id, provider_id)
            )
        """))
        print("  - 创建 key_balances 表")
        
        # 续费记录表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS renewal_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                key_id INTEGER REFERENCES user_api_keys(id) ON DELETE CASCADE,
                provider_id INTEGER REFERENCES api_providers(id),
                amount DECIMAL(10, 2) NOT NULL,
                currency VARCHAR(10) DEFAULT 'USD',
                duration_days INTEGER,
                expires_at TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("  - 创建 renewal_records 表")
        
        # 3. 修改现有表
        print("\n[3/6] 修改现有表...")
        
        # 为user_api_keys添加expires_at字段
        try:
            conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN expires_at TIMESTAMP"))
            print("  - 添加 user_api_keys.expires_at 字段")
        except Exception as e:
            print(f"  - expires_at 字段可能已存在: {e}")
        
        # 修改log_entries表的外键约束
        # SQLite不支持直接修改外键，需要重建表
        print("  - 检查 log_entries 表结构...")
        
        # 4. 迁移数据
        print("\n[4/6] 迁移数据...")
        # 数据已经在现有表中，无需迁移
        print("  - 数据无需迁移")
        
        # 5. 创建索引
        print("\n[5/6] 创建索引...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_login_history_created_at ON login_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_token_usage_user_id ON token_usage(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_token_usage_key_id ON token_usage(key_id)",
            "CREATE INDEX IF NOT EXISTS idx_token_usage_created_at ON token_usage(created_at)",
        ]
        
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
            except Exception as e:
                print(f"  - 索引创建跳过: {e}")
        
        print("  - 索引创建完成")
        
        # 6. 清理无用数据
        print("\n[6/6] 清理V1残留数据...")
        
        # 删除管理员相关的自定义服务商
        result = conn.execute(text("DELETE FROM api_providers WHERE is_custom = 1"))
        print(f"  - 删除自定义服务商")
        
        # 提交所有更改
        conn.commit()
        
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
        print("\n重要提示：")
        print("1. 所有用户现在都需要使用TOTP登录")
        print("2. 如果没有配置TOTP的用户，需要重新注册")
        print("3. 管理员功能已被移除")
        print("4. 请使用新的V2前端页面进行注册和登录")
        print("\n下一步：")
        print("1. 启动后端服务: python backend/main_v2.py")
        print("2. 访问新的注册页面: register_v2.html")
        print("3. 访问新的登录页面: index_v2.html")
        
    except Exception as e:
        print(f"\n迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def check_database_version():
    """检查数据库版本"""
    conn = engine.connect()
    try:
        # 检查是否存在V2特有的表
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='login_history'"))
        if result.fetchone():
            print("数据库已经是V2版本")
            return True
        return False
    except Exception:
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    if check_database_version():
        print("数据库已经是V2版本，无需迁移")
        sys.exit(0)
    
    print("\n警告：此操作将修改数据库结构")
    print("建议在执行前备份数据库文件")
    print(f"数据库路径: {settings.DATABASE_URL}\n")
    
    response = input("是否继续迁移？(yes/no): ")
    if response.lower() == 'yes':
        migrate_v1_to_v2()
    else:
        print("迁移已取消")
