"""直接测试数据库连接"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine
from sqlalchemy import text

print("Testing database connection...")
print(f"Database URL: {engine.url}")

try:
    with engine.connect() as conn:
        # 检查当前数据库
        result = conn.execute(text("SELECT current_database()"))
        print(f"Current database: {result.scalar()}")
        
        # 列出所有表
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        tables = [r[0] for r in result]
        print(f"Tables: {tables}")
        
        # 直接查询 totp_configs
        result = conn.execute(text("SELECT COUNT(*) FROM totp_configs"))
        print(f"totp_configs count: {result.scalar()}")
        
        # 查询 log_entries
        result = conn.execute(text("SELECT COUNT(*) FROM log_entries"))
        print(f"log_entries count: {result.scalar()}")
        
except Exception as e:
    print(f"Error: {e}")
