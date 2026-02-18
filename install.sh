#!/bin/bash
# API Key Manager 一键安装脚本 (Linux/Mac)

set -e

echo "=========================================="
echo "  API Key Manager 安装脚本"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到 Python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ 检测到 Python $PYTHON_VERSION"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未检测到 pip3，请先安装 pip"
    exit 1
fi
echo "✅ 检测到 pip3"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "📥 安装依赖..."
pip install -r backend/requirements.txt

# 创建环境变量文件
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  创建配置文件..."
    cp .env.example .env
    
    # 生成随机密钥
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
    ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
    ENCRYPTION_SALT=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')
    
    # 替换密钥
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-secret-key-at-least-32-characters-long/$SECRET_KEY/" .env
        sed -i '' "s/your-32-byte-encryption-key-here/$ENCRYPTION_KEY/" .env
        sed -i '' "s/your-16-byte-salt/$ENCRYPTION_SALT/" .env
    else
        sed -i "s/your-secret-key-at-least-32-characters-long/$SECRET_KEY/" .env
        sed -i "s/your-32-byte-encryption-key-here/$ENCRYPTION_KEY/" .env
        sed -i "s/your-16-byte-salt/$ENCRYPTION_SALT/" .env
    fi
    
    echo "✅ 配置文件已创建，密钥已自动生成"
else
    echo "✅ 配置文件已存在"
fi

echo ""
echo "=========================================="
echo "  ✅ 安装完成！"
echo "=========================================="
echo ""
echo "快速启动："
echo "  ./start.sh"
echo ""
echo "或手动启动："
echo "  source venv/bin/activate"
echo "  python backend/run_server.py"
echo ""
