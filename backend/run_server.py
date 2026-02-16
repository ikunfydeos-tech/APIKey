import uvicorn
import sys
import os
import shutil
from pathlib import Path

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
    print("Starting server...")
    sys.stdout.flush()
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
