# 前端和后端端口分离配置

## 配置说明

已将前端和后端服务器端口完全分离：

### 端口分配
- **前端服务器**: `localhost:5500` - 提供静态页面服务
- **后端服务器**: `localhost:8000` - 提供API服务

### 文件结构
```
api-manager/
├── backend/              # 后端代码
│   ├── main.py          # 后端API应用
│   └── run_server.py    # 后端服务器启动脚本
├── run_frontend.py      # 前端服务器启动脚本
├── start_all.py         # 一键启动所有服务脚本
└── index.html           # 前端页面（直接访问）
```

## 使用方法

### 方法1：一键启动（推荐）
```bash
python start_all.py
```
这将同时启动前端和后端服务器，并自动打开浏览器。

### 方法2：分别启动
```bash
# 启动前端服务器（5500端口）
python run_frontend.py

# 启动后端服务器（8000端口）
python backend/run_server.py
```

## 访问地址

- **前端主页**: http://localhost:5500
- **管理页面**: http://localhost:5500/dashboard.html
- **注册页面**: http://localhost:5500/register.html
- **后端API**: http://localhost:8000

## API端点

后端API运行在 `http://localhost:8000`，主要端点：
- `/health` - 健康检查
- `/api/auth/*` - 认证相关
- `/api/keys/*` - API密钥管理
- `/api/admin/*` - 管理员功能

## 配置说明

### 前端服务器 (`run_frontend.py`)
- 使用Python内置的HTTP服务器
- 自动打开浏览器
- 支持CORS跨域请求
- 提供所有静态资源（HTML、CSS、JS）

### 后端服务器 (`backend/run_server.py`)
- 使用FastAPI框架
- 运行在8000端口
- 只提供API服务
- 已清理缓存文件

## 注意事项

1. **端口占用**: 确保5500和8000端口未被其他程序占用
2. **依赖安装**: 确保已安装项目依赖：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. **数据库**: 后端需要数据库支持，请确保数据库服务已启动

## 故障排除

如果遇到问题：
1. 检查端口是否被占用：`netstat -ano | findstr :5500` 和 `netstat -ano | findstr :8000`
2. 查看启动脚本输出，确认服务是否正常启动
3. 检查浏览器控制台错误信息
4. 确认所有依赖已正确安装