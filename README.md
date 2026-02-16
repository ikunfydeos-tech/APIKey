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
  <a href="#部署指南">部署指南</a>
</p>

---

## 当前版本

**v0.2.0** - 私有部署版

---

## 为什么需要它？

如果你是 AI 开发者，可能面临这些问题：

- 🔑 OpenAI、Claude、Gemini... 每个平台都有 API Key，分散存储难以管理
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

### 👨‍💼 管理员后台
- 数据概览：用户数、密钥数、服务商统计
- 用户管理：列表、搜索、角色切换、启用/禁用
- 服务商管理：启用/禁用服务商
- 模型管理：添加、删除、筛选模型
- 配置同步：本地/远程配置同步

---

## 快速开始

### 方式一：一键配置（推荐）

```bash
# 运行环境检测脚本（自动检测环境、创建数据库、安装依赖）
python setup.py

# 启动服务
python start_all.py
```

> ⚠️ 运行 `setup.py` 前请确保已安装：
> - Python 3.10+
> - PostgreSQL 12+（服务已启动）
> 
> 默认数据库密码为 `123456`，可在 `backend/config.py` 中修改

---

### 方式二：手动配置

#### 前置要求

| 软件 | 版本要求 | 下载地址 |
|------|----------|----------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| PostgreSQL | 12+ | https://www.postgresql.org/download/ |

#### 步骤 1：安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 步骤 2：创建数据库

```sql
-- 连接 PostgreSQL
psql -U postgres

-- 创建数据库
CREATE DATABASE llm_api_manager;

-- 退出
\q
```

#### 步骤 3：初始化数据库表

```bash
psql -U postgres -d llm_api_manager -f sql/create_tables.sql
psql -U postgres -d llm_api_manager -f sql/migrate_add_category.sql
psql -U postgres -d llm_api_manager -f sql/migrate_add_user_role.sql
```

#### 步骤 4：配置环境变量

创建 `backend/.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/llm_api_manager

# JWT 密钥（请修改为随机字符串）
SECRET_KEY=your-secret-key-change-this-in-production

# 加密密钥（请修改为随机字符串）
ENCRYPTION_KEY=your-encryption-key-change-this
```

#### 步骤 5：启动服务

```bash
# 启动后端
cd backend
python run_server.py

# 启动前端（另一个终端）
python run_frontend.py
```

#### 步骤 6：访问应用

打开浏览器访问：`http://localhost:5500`

默认管理员账户：`admin` / `Admin123456`

---

### 方式三：Docker 部署（推荐生产环境）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

启动后访问：`http://localhost`

#### 环境变量配置

创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
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
├── admin.html          # 管理员后台
├── terms.html          # 服务条款
├── css/                # 样式文件
├── js/                 # 前端逻辑
├── backend/            # 后端服务
│   ├── main.py         # FastAPI 入口
│   ├── config.py       # 配置管理
│   ├── models.py       # 数据模型
│   ├── auth.py         # 认证模块
│   ├── routers/        # API 路由
│   └── requirements.txt
└── sql/                # 数据库脚本
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
| `/api/keys` | GET/POST | 密钥列表/添加 | ✅ |
| `/api/keys/{id}` | PUT/DELETE | 更新/删除密钥 | ✅ |
| `/api/keys/test` | POST | 测试密钥连接 | ✅ |
| `/api/admin/users` | GET | 用户管理 | Admin |
| `/api/admin/providers` | GET | 服务商管理 | Admin |
| `/api/admin/models` | GET/POST | 模型管理 | Admin |

---

## 路线图

### v0.2.0 (当前)
- [x] 用户注册/登录
- [x] API 密钥加密存储
- [x] 服务商预设
- [x] 模型选择
- [x] 测试连接
- [x] 管理员后台
- [x] Docker 部署支持

### v0.3.0 (计划中)
- [ ] 使用统计真实数据
- [ ] 单元测试

### v0.4.0 (计划中)
- [ ] 团队协作
- [ ] 权限管理

---

## 常见问题

### Q: 没有安装 PostgreSQL 怎么办？

**A:** 请先安装 PostgreSQL：
- **Windows**: 下载 [PostgreSQL 安装包](https://www.postgresql.org/download/windows/)
- **macOS**: `brew install postgresql && brew services start postgresql`
- **Linux**: `sudo apt install postgresql postgresql-contrib`

### Q: 如何创建数据库？

**A:** 命令行创建：
```bash
psql -U postgres
CREATE DATABASE llm_api_manager;
\q
```

### Q: 启动后端报数据库连接错误？

**A:** 请确认：
1. PostgreSQL 服务已启动
2. 数据库 `llm_api_manager` 已创建
3. `backend/config.py` 中的数据库连接配置正确

### Q: 如何修改加密密钥？

**A:** 修改 `backend/config.py` 中的 `ENCRYPTION_KEY`。注意：修改后之前加密的密钥将无法解密。

---

## 版权声明

**© 2026 API Key Manager. All Rights Reserved.**

本软件为私有软件，未经授权不得复制、修改、传播或用于商业目的。

---

## 联系方式

- 提交 Issue: https://gitcode.com/IkunWindow/APIManagementPlatform/issues
- 仓库地址: https://gitcode.com/IkunWindow/APIManagementPlatform
