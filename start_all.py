import subprocess
import sys
import time
import threading
import requests
import os
from pathlib import Path

# 项目根目录
PROJECT_DIR = Path(__file__).parent
os.chdir(PROJECT_DIR)

def start_backend():
    """启动后端服务器"""
    print("=" * 50)
    print("启动后端服务器 (端口: 8000)")
    print("=" * 50)
    try:
        subprocess.run([sys.executable, "backend/run_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n后端服务器已停止")
    except Exception as e:
        print(f"后端服务器启动失败: {e}")

def start_frontend():
    """启动前端服务器"""
    print("=" * 50)
    print("启动前端服务器 (端口: 5500)")
    print("=" * 50)
    try:
        subprocess.run([sys.executable, "run_frontend.py"], check=True)
    except KeyboardInterrupt:
        print("\n前端服务器已停止")
    except Exception as e:
        print(f"前端服务器启动失败: {e}")

def check_backend_health():
    """检查后端健康状态"""
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✓ 后端服务器运行正常")
                return True
        except:
            pass
        time.sleep(1)
    print("✗ 后端服务器启动超时")
    return False

def main():
    print("API密钥管理平台 - 启动所有服务")
    print("项目目录:", PROJECT_DIR)
    print()
    
    # 启动后端服务器
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # 等待后端启动
    time.sleep(3)
    
    # 检查后端健康状态
    if not check_backend_health():
        print("后端启动失败，退出程序")
        return
    
    # 启动前端服务器
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()
    
    print()
    print("=" * 50)
    print("所有服务已启动完成!")
    print("=" * 50)
    print(f"前端地址: http://localhost:5500")
    print(f"后端API:  http://localhost:8000")
    print(f"管理地址: http://localhost:5500/dashboard.html")
    print()
    print("按 Ctrl+C 停止所有服务")
    print("=" * 50)
    print()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止所有服务...")
        print("程序已退出")

if __name__ == "__main__":
    main()