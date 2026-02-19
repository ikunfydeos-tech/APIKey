import uvicorn
import sys
import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine, text
from config import settings

def clear_pycache(base_dir: Path):
    """清理所有 __pycache__ 目录"""
    cleared = 0
    for pycache in base_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            cleared += 1
            print(f"已清理: {pycache}")
        except Exception as e:
            print(f"清理失败 {pycache}: {e}")
    return cleared

def clear_pyc_files(base_dir: Path):
    """清理所有 .pyc 文件"""
    cleared = 0
    for pyc in base_dir.rglob("*.pyc"):
        try:
            pyc.unlink()
            cleared += 1
        except Exception:
            pass
    return cleared

def create_base_tables(engine):
    """创建基础表（如果不存在）"""
    from database import Base
    from models_v2 import User, ApiProvider, ApiModel, UserApiKey, LogEntry, TOTPConfig, LoginHistory, TokenUsage, KeyBalance, RenewalRecord
    
    print("创建基础数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 基础表创建完成")

def init_default_providers(engine):
    """初始化默认 API providers"""
    from sqlalchemy.orm import Session
    from models_v2 import ApiProvider
    
    with Session(engine) as db:
        existing = db.query(ApiProvider).first()
        if not existing:
            providers = [
                ApiProvider(name='openai', display_name='OpenAI', base_url='https://api.openai.com/v1', description='OpenAI GPT models API', icon='openai', sort_order=1),
                ApiProvider(name='anthropic', display_name='Anthropic', base_url='https://api.anthropic.com/v1', description='Claude models API', icon='anthropic', sort_order=2),
                ApiProvider(name='google', display_name='Google AI', base_url='https://generativelanguage.googleapis.com/v1', description='Google Gemini models API', icon='google', sort_order=3),
                ApiProvider(name='deepseek', display_name='DeepSeek', base_url='https://api.deepseek.com/v1', description='DeepSeek AI models API', icon='deepseek', sort_order=4),
                ApiProvider(name='zhipu', display_name='Zhipu AI', base_url='https://open.bigmodel.cn/api/paas/v4', description='Zhipu GLM models API', icon='zhipu', sort_order=5),
            ]
            db.add_all(providers)
            db.commit()
            print("✅ 预设 API providers 已添加")
        else:
            print("✅ API providers 已存在")

def run_database_migrations(engine):
    """执行数据库迁移"""
    print("=" * 50)
    print("执行数据库迁移...")
    print("=" * 50)
    
    try:
        # 读取并执行迁移脚本
        migration_dir = Path(__file__).parent / "sql"
        migration_script = migration_dir / "migrate_add_balance_tables.sql"
        
        if migration_script.exists():
            with open(migration_script, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            with engine.connect() as conn:
                # 分割SQL语句并执行
                statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
                for statement in statements:
                    if statement:
                        try:
                            conn.execute(text(statement))
                        except Exception as e:
                            # 忽略已存在的索引错误
                            if "already exists" not in str(e).lower():
                                print(f"警告: {e}")
                conn.commit()
            
            print("✅ 数据库迁移执行成功")
        else:
            print("⚠️  迁移脚本不存在，跳过迁移")
            
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        raise

def initialize_database():
    """初始化数据库"""
    print("=" * 50)
    print("初始化数据库...")
    print("=" * 50)
    
    try:
        # 确保数据库文件存在
        if settings.USE_SQLITE:
            db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
            if not db_path.parent.exists():
                db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建数据库引擎
        if settings.USE_SQLITE:
            engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # 1. 先创建基础表
        create_base_tables(engine)
        
        # 2. 初始化默认数据
        init_default_providers(engine)
        
        # 3. 执行数据库迁移
        run_database_migrations(engine)
        
        print("✅ 数据库初始化完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise

if __name__ == "__main__":
    # 获取当前脚本所在目录
    backend_dir = Path(__file__).parent
    
    print("=" * 50)
    print("清理 Python 缓存...")
    print("=" * 50)
    
    # 清理 __pycache__ 目录
    cache_dirs = clear_pycache(backend_dir)
    # 清理 .pyc 文件
    pyc_files = clear_pyc_files(backend_dir)
    
    print(f"已清理 {cache_dirs} 个缓存目录, {pyc_files} 个 .pyc 文件")
    print("=" * 50)
    print("初始化数据库...")
    print("=" * 50)
    
    # 初始化数据库
    initialize_database()
    
    print("=" * 50)
    print("启动服务器...")
    print("=" * 50)
    sys.stdout.flush()
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
