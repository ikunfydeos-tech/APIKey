#!/usr/bin/env python3
"""
API Key Manager 环境检测和数据库初始化脚本
运行方式: python setup.py
"""

import subprocess
import sys
import os

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"✓ Python 版本: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  ⚠️ 警告: 推荐 Python 3.10+")
        return False
    return True

def check_postgresql():
    """检查 PostgreSQL 是否安装"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ PostgreSQL 已安装: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("✗ PostgreSQL 未安装")
    print("  请先安装 PostgreSQL:")
    print("  - Windows: https://www.postgresql.org/download/windows/")
    print("  - macOS: brew install postgresql")
    print("  - Linux: sudo apt install postgresql")
    return False

def check_database_connection():
    """检查数据库连接"""
    try:
        import psycopg2
        # 尝试默认连接
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="123456",
            database="postgres"
        )
        conn.close()
        print("✓ 数据库连接成功")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        print("  请确保 PostgreSQL 服务已启动，并检查连接配置")
        return False

def check_database_exists():
    """检查数据库是否存在"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="123456",
            database="llm_api_manager"
        )
        conn.close()
        print("✓ 数据库 'llm_api_manager' 已存在")
        return True
    except Exception:
        print("✗ 数据库 'llm_api_manager' 不存在")
        return False

def create_database():
    """创建数据库"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="123456",
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE llm_api_manager;")
        cursor.close()
        conn.close()
        print("✓ 数据库 'llm_api_manager' 创建成功")
        return True
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False

def init_tables():
    """初始化数据表"""
    sql_file = os.path.join(os.path.dirname(__file__), 'sql', 'create_tables.sql')
    if not os.path.exists(sql_file):
        print(f"✗ SQL 文件不存在: {sql_file}")
        return False
    
    try:
        result = subprocess.run([
            'psql', '-U', 'postgres', '-d', 'llm_api_manager',
            '-f', sql_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 数据表初始化成功")
            return True
        else:
            print(f"✗ 数据表初始化失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 执行 SQL 失败: {e}")
        print("  请手动执行: psql -U postgres -d llm_api_manager -f sql/create_tables.sql")
        return False

def install_dependencies():
    """安装 Python 依赖"""
    requirements = os.path.join(os.path.dirname(__file__), 'backend', 'requirements.txt')
    if not os.path.exists(requirements):
        print(f"✗ requirements.txt 不存在: {requirements}")
        return False
    
    print("正在安装 Python 依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', requirements], check=True)
        print("✓ Python 依赖安装成功")
        return True
    except Exception as e:
        print(f"✗ 安装依赖失败: {e}")
        return False

def main():
    print("=" * 50)
    print("API Key Manager 环境检测")
    print("=" * 50)
    print()
    
    # 检查 Python
    print("[1/6] 检查 Python 版本...")
    check_python_version()
    print()
    
    # 检查 PostgreSQL
    print("[2/6] 检查 PostgreSQL...")
    pg_ok = check_postgresql()
    if not pg_ok:
        print("\n请先安装 PostgreSQL 后再运行此脚本")
        return
    print()
    
    # 检查数据库连接
    print("[3/6] 检查数据库连接...")
    db_conn = check_database_connection()
    if not db_conn:
        print("\n请确保 PostgreSQL 服务已启动")
        print("Windows: 在服务中启动 postgresql-x64-18")
        print("macOS: brew services start postgresql")
        print("Linux: sudo systemctl start postgresql")
        return
    print()
    
    # 检查/创建数据库
    print("[4/6] 检查数据库...")
    if not check_database_exists():
        print("正在创建数据库...")
        if not create_database():
            return
    print()
    
    # 初始化表
    print("[5/6] 初始化数据表...")
    init_tables()
    print()
    
    # 安装依赖
    print("[6/6] 安装 Python 依赖...")
    install_dependencies()
    print()
    
    print("=" * 50)
    print("环境配置完成！")
    print("=" * 50)
    print()
    print("启动方式:")
    print("  后端: cd backend && python run_server.py")
    print("  前端: python run_frontend.py")
    print("  或:   python start_all.py")
    print()
    print("访问地址: http://localhost:5500")

if __name__ == '__main__':
    main()
