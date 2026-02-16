# API Key Manager

<p align="center">
  <img src="api-manager-new-color.png" alt="API Key Manager" width="400">
</p>

<p align="center">
  <strong>🔐 一站式 API 密钥管理平台</strong>
</p>

<p align="center">
  安全存储 · 一键配置 · 集中管理
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#部署指南">部署指南</a> •
  <a href="#已知问题">已知问题</a>
</p>

---

## 当前版本

**v0.1.0-beta** - 早期测试版本

> ⚠️ 这是早期测试版本，核心功能可用，但可能存在一些问题。欢迎提 Issue 反馈！

---

## 为什么需要它？

如果你是 AI 开发者，可能面临这些问题：

- 🔑 OpenAI��Claude、Gemini... 每个平台都有 API Key，分散存储难以管理
- 😰 密钥明文保存在笔记、Excel 中，存在泄露风险
- 📋 每次配置新工具都要翻找密钥、复制粘贴
- 🤔 模型 ID 太长记不住，`gpt-4o` 还是 `gpt-4-turbo`？

**API Key Manager** 解决这些痛点，让你专注于开发，而非密钥管理。

---

## 功能特性

### 🔐 安全存储
- AES-256 加密存储所有 API 密钥
- 密钥永不明文显示，只展示预览（如 `sk-abc...xyz`）
- 支持一键复制，用完即走

### 🏷️ 服务商预设
内置 10+ 主流 AI 服务商配置：

| 服务商 | Base URL |
|--------|----------|
| OpenAI | `https://api.openai.com/v1` |
| Anthropic | `https://api.anthropic.com` |
| Google AI | `https://generativelanguage.googleapis.com` |
| DeepSeek | `https://api.deepseek.com` |
| 智谱 AI | `https://open.bigmodel.cn/api/paas/v4` |
| Moonshot | `https://api.moonshot.cn/v1` |
| 百度文心 | `https://aip.baidubce.com` |
| 阿里通义 | `https://dashscope.aliyuncs.com/api/v1` |
| Azure OpenAI | 自定义配置 |
| 自定义 | 支持添加任意服务商 |

### 🤖 模型选择
- 预设各服务商常用模型
- 模型分类标签（对话、代码、长文本、多模态）
- 一键复制模型 ID

### ✅ 测试连接
- 添加密钥时可测试有效性
- 实时验证密钥是否可用

### 📊 使用统计
- 密钥使用概览
- Token 消耗统计
- 趋势图表展示

---

## 快速开始

### 方式一：一键配置（推荐新手）

```bash
# 1. 克隆项目
git clone https://gitcode.com/IkunWindow/APIManagementPlatform.git
cd APIManagementPlatform

# 2. 运行环境检测脚本（自动检测环境、创建数据库、安装依赖）
python setup.py

# 3. 启动服务
python start_all.py
```

> ⚠️ 运行 `setup.py` 前请确保已安装：
> - Python 3.10+
> - PostgreSQL 12+（服务已启动）
> 
> 默认数据库密码为 `123456`，可在 `backend/config.py` 中修改

---

### 方式二：手动配置（开发者）

#### 前置要求

| 软件 | 版本要求 | 下载地址 |
|------|----------|----------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| PostgreSQL | 12+ | https://www.postgresql.org/download/ |

#### 步骤 1：克隆项目

```bash
git clone https://gitcode.com/IkunWindow/APIManagementPlatform.git
cd APIManagementPlatform
```

#### 步骤 2：安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 步骤 3：创建数据库

打开 PostgreSQL 命令行或使用图形工具：

```sql
-- 连接 PostgreSQL
psql -U postgres

-- 创建数据库
CREATE DATABASE llm_api_manager;

-- 退出
\q
```

#### 步骤 4：初始化数据库表

```bash
# 在项目根目录执行
psql -U postgres -d llm_api_manager -f sql/create_tables.sql

# 执行模型数据初始化（可选）
psql -U postgres -d llm_api_manager -f sql/migrate_add_category.sql
```

#### 步骤 5：配置环境变量

创建 `backend/.env` 文件：

```env
# 数据库配置（请修改密码）
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/llm_api_manager

# JWT 密钥（请修改为随机字符串）
SECRET_KEY=your-secret-key-change-this-in-production

# 加密密钥（请修改为随机字符串）
ENCRYPTION_KEY=your-encryption-key-change-this
```

#### 步骤 6：启动服务

**启动后端（终端 1）**：

```bash
cd backend
python run_server.py
```

看到以下输出表示启动成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**启动前端（终端 2）**：

```bash
cd api-manager
python run_frontend.py
```

或者使用 VS Code Live Server 插件直接打开 `index.html`。

#### 步骤 7：访问应用

打开浏览器访问：`http://localhost:5500`

---

### 方式三：Docker 部署（推荐生产环境）

#### 一键启动

```bash
# 克隆项目
git clone https://gitcode.com/IkunWindow/APIManagementPlatform.git
cd APIManagementPlatform

# 启动所有服务（数据库 + 后端 + 前端）
docker-compose up -d

# 查看服务状态
docker-compose ps
```

启动后访问：`http://localhost`

#### 环境变量配置

创建 `.env` 文件（可选）：

```env
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
```

#### Docker 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | Nginx 前端服务 |
| backend | 8000 | FastAPI 后端服务 |
| db | 5432 | PostgreSQL 数据库 |

#### 常用命令

```bash
# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重新构建
docker-compose up -d --build

# 进入数据库
docker-compose exec db psql -U postgres -d llm_api_manager
```

---

## 部署指南

### 生产环境配置清单

| 配置项 | 说明 | 必须 |
|--------|------|------|
| 修改数据库密码 | 不要使用默认密码 | ✅ |
| 修改 JWT_SECRET_KEY | 使用随机字符串 | ✅ |
| 修改 ENCRYPTION_KEY | 使用随机字符串 | ✅ |
| 启用 HTTPS | 使用 Let's Encrypt | ✅ |
| 配置防火墙 | 只开放 80/443 端口 | ✅ |

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /var/www/api-manager;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd 服务配置

创建 `/etc/systemd/system/api-manager.service`：

```ini
[Unit]
Description=API Key Manager Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/api-manager/backend
ExecStart=/usr/bin/python3 run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable api-manager
sudo systemctl start api-manager
```

---

## 已知问题

> 以下是当前版本的已知问题，我们正在积极解决中。

| 问题 | 状态 | 说明 |
|------|------|------|
| 使用统计为模拟数据 | 🔄 开发中 | 目前显示的是模拟数据，真实数据接入开发中 |
| 缺少单元测试 | 📋 计划中 | 后端 API 测试覆盖率为 0 |
| ~~缺少 Dockerfile~~ | ~~Docker 部署配置待添加~~ | ~~中~~ ✅ ���完成 |
| 管理员功能未完善 | 📋 计划中 | 管理员权限校验需要执行数据库迁移 |

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | HTML + CSS + JavaScript | 原生 |
| 后端 | Python + FastAPI | 3.13 / 0.115.0 |
| 数据库 | PostgreSQL | 18.1 |
| 认证 | JWT | python-jose |
| 加密 | bcrypt + Fernet | AES-256 |

---

## 项目结构

```
api-manager/
├── index.html          # 登录页面
├── register.html       # 注册页面
├── dashboard.html      # 主控制台
├── terms.html          # 服务条款
├── css/                # 样式文件
│   ├── style.css       # 登录页样式
│   ├── register.css    # 注册页样式
│   └── dashboard.css   # 控制台样式
├── js/                 # 前端逻辑
│   ├── script.js       # 登录页逻辑
│   ├── register.js     # 注册页逻辑
│   └── dashboard.js    # 控制台逻辑
├── backend/            # 后端服务
│   ├── main.py         # FastAPI 入口
│   ├── config.py       # 配置管理
│   ├── models.py       # 数据模型
│   ├── auth.py         # 认证模块
│   ├── routers/        # API 路由
│   │   ├── auth.py     # 认证路由
│   │   ├── keys.py     # 密钥管理
│   │   └── admin.py    # 管理员路由
│   └── requirements.txt
└── sql/                # 数据库脚本
    ├── create_tables.sql
    └── migrate_*.sql
```

---

## API 文档

启动后端后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 主要接口

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/register` | POST | 用户注册 | ❌ |
| `/api/login` | POST | 用户登录 | ❌ |
| `/api/me` | GET | 获取当前用户 | ✅ |
| `/api/keys` | GET | 获取密钥列表 | ✅ |
| `/api/keys` | POST | 添加新密钥 | ✅ |
| `/api/keys/{id}` | PUT | 更新密钥 | ✅ |
| `/api/keys/{id}` | DELETE | 删除密钥 | ✅ |
| `/api/keys/test` | POST | 测试密钥连接 | ✅ |
| `/api/keys/providers` | GET | 获取服务商列表 | ✅ |

---

## 路线图

### v0.1.0 (当前)
- [x] 用户注册/登录
- [x] API 密钥加密存储
- [x] 服务商预设
- [x] 模型选择
- [x] 测试连接
- [x] 使用统计（模拟数据）

### v0.2.0 (计划中)
- [ ] 使用统计真实数据
- [ ] Docker 部署支持
- [ ] 单元测试

### v0.3.0 (计划中)
- [ ] 团队协作
- [ ] 权限管理

### v1.0.0 (未来)
- [ ] 代理服务器
- [ ] 私有部署方案

---

## 贡献指南

欢迎贡献代码、报告 Bug 或提出新功能建议！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 常见问题

### Q: 没有安装 PostgreSQL 怎么办？

**A:** 请先安装 PostgreSQL：
- **Windows**: 下载 [PostgreSQL 安装包](https://www.postgresql.org/download/windows/)，安装时记住设置的密码
- **macOS**: `brew install postgresql && brew services start postgresql`
- **Linux**: `sudo apt install postgresql postgresql-contrib`

安装后启动服务，Windows 用户可在"服务"中找到 `postgresql-x64-xx` 并启动。

### Q: 如何创建数据库？

**A:** 方式一：使用 pgAdmin 图形界面创建

方式二：命令行创建
```bash
# 连接 PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE llm_api_manager;

# 退出
\q
```

### Q: 启动后端报数据库连接错误？

**A:** 请确认：
1. PostgreSQL 服务已启动
2. 数据库 `llm_api_manager` 已创建
3. `backend/config.py` 中的数据库连接配置正确
4. 密码正确（默认为 `123456`，如果你安装时设置了其他密码，需要修改配置）

### Q: 前端无法连接后端？

**A:** 请确认：
1. 后端服务已启动在 `localhost:8000`
2. 前端 `js/*.js` 中的 `API_BASE_URL` 配置正确

### Q: 如何修改加密密钥？

**A:** 修改 `backend/config.py` 中的 `ENCRYPTION_KEY`。注意：修改后之前加密的密钥将无法解密。

### Q: 运行 setup.py 提示错误？

**A:** 常见原因：
1. PostgreSQL 未安装或未启动
2. 数据库密码不是默认的 `123456`，需要先修改 `backend/config.py`
3. Python 版本过低，需要 3.10+

---

## 许可证

[MIT License](LICENSE)

---

## 联系方式

- 提交 Issue: https://gitcode.com/IkunWindow/APIManagementPlatform/issues
- 仓库地址: https://gitcode.com/IkunWindow/APIManagementPlatform

---

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Lucide Icons](https://lucide.dev/) - 美观的图标库
- [Chart.js](https://www.chartjs.org/) - 图表库