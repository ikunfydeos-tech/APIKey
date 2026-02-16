import subprocess
import sys
import time
import threading
import requests
import os
from pathlib import Path

def test_setup():
    print("测试前端和后端端口分离配置")
    print("=" * 50)
    
    # 1. 检查后端服务器配置
    backend_main = Path("backend/main.py")
    if backend_main.exists():
        with open(backend_main, 'r', encoding='utf-8') as f:
            content = f.read()
            if "/css" in content and "/js" in content:
                print("❌ 后端仍包含静态文件挂载")
            else:
                print("✅ 后端已移除静态文件挂载")
    
    # 2. 检查前端服务器配置
    frontend_run = Path("run_frontend.py")
    if frontend_run.exists():
        print("✅ 前端服务器脚本已创建")
    else:
        print("❌ 前端服务器脚本不存在")
    
    # 3. 检查启动脚本
    start_all = Path("start_all.py")
    if start_all.exists():
        print("✅ 启动脚本已创建")
    else:
        print("❌ 启动脚本不存在")
    
    # 4. 测试端口配置
    print("\n端口配置:")
    print("  前端: 5500")
    print("  后端: 8000")
    
    print("\n使用方法:")
    print("  1. 启动所有服务: python start_all.py")
    print("  2. 或分别启动:")
    print("     - 前端: python run_frontend.py")
    print("     - 后端: python backend/run_server.py")
    
    print("\n访问地址:")
    print("  前端: http://localhost:5500")
    print("  后端API: http://localhost:8000")
    print("  管理页面: http://localhost:5500/dashboard.html")

if __name__ == "__main__":
    test_setup()