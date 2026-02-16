# API Key Manager - 后端服务
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/
COPY sql/ ./sql/

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/llm_api_manager
ENV SECRET_KEY=your-secret-key-change-in-production
ENV ENCRYPTION_KEY=your-encryption-key-change-in-production

# 暴露端口
EXPOSE 8000

# 启动命令
WORKDIR /app/backend
CMD ["python", "run_server.py"]
