#!/bin/bash
# API Key Manager 启动脚本 (Linux/Mac)

cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 未检测到虚拟环境，请先运行 ./install.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ 未检测到配置文件，请先运行 ./install.sh"
    exit 1
fi

echo "🚀 启动 API Key Manager..."
echo ""
echo "访问地址:"
echo "  前端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"

# 启动服务
python backend/run_server.py
