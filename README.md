# API Key Manager

<p align="center">
  <img src="api-manager-new-color.png" alt="API Key Manager" width="400">
</p>

<p align="center">
  <strong>🔐 一站式 API 密钥管理平台</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI"></a>
  <img src="https://img.shields.io/badge/数据库-SQLite%20%7C%20PostgreSQL-orange" alt="Database">
</p>

<p align="center">
  <strong>⚡ 3 分钟快速部署</strong> · 无需安装数据库 · 开箱即用
</p>

<p align="center">
  <strong>简体中文</strong> | <a href="README_EN.md">English</a>
</p>

---

## ✨ 特点

- 🚀 **快速部署** — 一键安装脚本，无需手动配置
- 💾 **零依赖启动** — 默认使用 SQLite，无需安装数据库
- 🔐 **银行级加密** — AES-256 加密存储，密钥永不明文
- 🏷️ **预设服务商** — 支持 OpenAI、Claude、Gemini、DeepSeek 等 10+ 平台
- 🔒 **双因素认证** — 支持 TOTP 二次验证
- 📱 **响应式设计** — 支持手机、平板、电脑访问

---

## ⚡ 快速开始

### Windows

```powershell
# 1. 克隆项目
git clone https://github.com/ikunfydeos-tech/APIKey.git
cd APIKey

# 2. 一键安装（右键 -> 使用 PowerShell 运行）
.\install.ps1

# 3. 启动服务
.\start.ps1

# 4. 访问 http://localhost:8000
```

### Linux / Mac

```bash
# 1. 克隆项目
git clone https://github.com/ikunfydeos-tech/APIKey.git
cd APIKey

# 2. 一键安装
chmod +x install.sh && ./install.sh

# 3. 启动服务
./start.sh

# 4. 访问 http://localhost:8000
```

---

## 🐳 Docker 部署

### 方式一：SQLite 模式（推荐个人使用）

```bash
# 一键启动（最简单）
docker-compose -f docker-compose.sqlite.yml up -d

# 访问 http://localhost:8000
# 数据存储在 ./data/api_manager.db
```

### 方式二：PostgreSQL 模式（推荐生产环境）

```bash
# 1. 创建配置文件
cp .env.example .env

# 2. 编辑 .env 设置必填项：
#    - SECRET_KEY（至少 32 字符）
#    - ENCRYPTION_KEY（32 字节）
#    - ENCRYPTION_SALT（16 字节）
#    - DB_PASSWORD（数据库密码）

# 3. 启动服务
docker-compose up -d

# 访问 http://localhost:8000
```

### 数据库选择对比

| 数据库 | 适用场景 | 启动命令 |
|--------|----------|----------|
| **SQLite** | 个人使用、测试、开发 | `docker-compose -f docker-compose.sqlite.yml up -d` |
| **PostgreSQL** | 生产环境、多用户、高并发 | `docker-compose up -d` |

---

## 📸 截图

<p align="center">
  <img src="screenshot-dashboard.png" alt="Dashboard" width="600">
</p>

---

## 🔧 配置说明

### 环境变量

首次运行 `install.ps1` 或 `install.sh` 会自动创建 `.env` 文件并生成随机密钥。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 | SQLite（开发）/ PostgreSQL（生产） |
| `SECRET_KEY` | JWT 密钥 | 自动生成 |
| `ENCRYPTION_KEY` | 加密密钥 | 自动生成 |
| `ENCRYPTION_SALT` | 加密盐值 | 自动生成 |
| `CORS_ORIGINS` | 允许的域名 | `*` |

### 切换到 PostgreSQL（生产环境推荐）

```bash
# .env 文件
DATABASE_URL=postgresql://user:password@localhost:5432/api_manager

# 安装 PostgreSQL 驱动
pip install psycopg[binary]
```

---

## 🎯 核心功能

### 🔐 安全加密存储

- **AES-256 加密**：所有密钥采用银行级加密存储
- **密钥预览**：只显示 `sk-abc...xyz`，永不明文
- **一键复制**：用完即走，不留痕迹

### 🏷️ 内置服务商

| 服务商 | 密钥存储 | 模型选择 | 连接测试 |
|--------|:-------:|:-------:|:-------:|
| OpenAI | ✅ | ✅ | ✅ |
| Anthropic (Claude) | ✅ | ✅ | ✅ |
| Google AI (Gemini) | ✅ | ✅ | ✅ |
| DeepSeek | ✅ | ✅ | ✅ |
| 智谱 AI | ✅ | ✅ | ✅ |
| Moonshot | ✅ | ✅ | ✅ |
| 百度文心 | ✅ | ✅ | - |
| 阿里通义 | ✅ | ✅ | - |
| Azure OpenAI | ✅ | ✅ | - |
| 自定义服务商 | ✅ | ✅ | ✅ |

### 🔒 安全特性

- **TOTP 双因素认证** — 支持 Google Authenticator 等
- **登录保护** — 多次失败自动锁定账户
- **操作日志** — 完整审计追踪
- **速率限制** — 防止暴力攻击

---

## 📁 项目结构

```
APIKey/
├── backend/              # 后端服务
│   ├── routers/          # API 路由
│   ├── models.py         # 数据模型
│   ├── config.py         # 配置管理
│   └── database.py       # 数据库连接
├── css/                  # 样式文件
├── js/                   # 前端脚本
├── *.html                # 页面文件
├── install.ps1           # Windows 安装脚本
├── install.sh            # Linux/Mac 安装脚本
├── start.ps1             # Windows 启动脚本
├── start.sh              # Linux/Mac 启动脚本
├── docker-compose.yml    # Docker 配置（PostgreSQL）
├── docker-compose.sqlite.yml  # Docker 配置（SQLite）
└── LICENSE               # MIT 许可证
```

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | SQLite / PostgreSQL |
| ORM | SQLAlchemy |
| 认证 | JWT + TOTP |
| 加密 | AES-256 |
| 前端 | 原生 HTML/CSS/JS |

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📋 常见问题

### Q: 默认数据库是什么？

**A:** 开发环境默认使用 SQLite，无需安装任何数据库。生产环境推荐切换到 PostgreSQL。

### Q: 密钥安全吗？

**A:** 采用 AES-256 加密存储，密钥永不明文显示。即使是管理员也无法查看你的密钥原文。

### Q: 可以自定义服务商吗？

**A:** 可以。支持 OpenAI 兼容格式的自定义服务商。

### Q: 如何备份数据？

**A:** SQLite 用户直接复制 `api_manager.db` 文件即可。PostgreSQL 用户使用 `pg_dump`。

---

## 📄 许可证

[MIT License](LICENSE) - 可自由商用、修改、分发。

---

## 📧 联系方式

- 🐛 提交 Issue：[GitHub Issues](https://github.com/ikunfydeos-tech/APIKey/issues)
- 📧 邮箱：ikunfydeos@163.com

---

<p align="center">
  <strong>如果这个项目对你有帮助，请给一个 ⭐️ Star 支持！</strong>
</p>
