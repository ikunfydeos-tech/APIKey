# API Key Manager

<p align="center">
  <img src="api-manager-new-color.png" alt="API Key Manager" width="400">
</p>

<p align="center">
  <strong>🔐 一站式 API 密钥托管平台</strong>
</p>

<p align="center">
  <a href="#许可证"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="#技术栈"><img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"></a>
  <a href="#技术栈"><img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI"></a>
  <a href="#托管服务"><img src="https://img.shields.io/badge/托管服务-可用-brightgreen.svg" alt="Hosted"></a>
</p>

<p align="center">
  开源 · 自托管 · 或使用我们的托管服务
</p>

---

## 简介

**API Key Manager** 是一款专为 AI 开发者打造的 API 密钥管理平台。

你是否曾为以下问题烦恼？

- 🔑 OpenAI、Claude、Gemini、DeepSeek... 密钥散落各处
- 😰 明文存储在笔记、Excel 中，担心泄露
- 📋 每次配置新工具都要翻找复制
- 🤔 模型 ID 太长记不住
- 💻 换电脑后密钥要重新整理

**API Key Manager** 帮你一站式解决！

---

## 托管服务

不想自己部署？我们提供托管服务：

**在线地址**：🚧 即将上线，敬请期待

### 版本对比

| 功能 | 免费版 | Pro 版 (¥19/月) |
|------|--------|-----------------|
| 密钥数量 | 10 个 | 无限 |
| 服务商数量 | 10+ | 10+ |
| 自定义服务商 | ❌ | ✅ |
| 使用统计 | 基础 | 详细 |
| 自动备份 | ❌ | 每日 |
| 多设备同步 | ✅ | ✅ |

---

## 自托管部署

如果你想自己部署，完全免费。

### 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.10+ / FastAPI |
| 数据库 | PostgreSQL |
| 前端 | 原生 HTML/CSS/JS |
| 加密 | AES-256 |
| 认证 | JWT + TOTP 双因素 |

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/ikunfydeos-tech/APIKey.git
cd api-key-manager

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r backend/requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的配置

# 5. 初始化数据库
python backend/run_server.py

# 6. 访问
# 前端: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 环境变量

```bash
# 必需
DATABASE_URL=postgresql://user:password@localhost:5432/api_manager
SECRET_KEY=your-secret-key-at-least-32-chars
ENCRYPTION_KEY=your-32-byte-encryption-key
ENCRYPTION_SALT=your-16-byte-salt
CORS_ORIGINS=https://yourdomain.com

# 可选
ENV=production
RATE_LIMIT_PER_MINUTE=60
```

### Docker 部署

```bash
# 使用 Docker Compose
docker-compose up -d
```

---

## 核心功能

### 🔐 安全加密存储

- **AES-256 加密**：所有密钥采用银行级加密存储
- **密钥预览**：只显示 `sk-abc...xyz`，永不明文
- **一键复制**：用完即走，不留痕迹

### 🏷️ 内置服务商配置

预设 10+ 主流 AI 平台，开箱即用：

| 服务商 | 支持功能 |
|--------|----------|
| OpenAI | ✅ 密钥存储 · 模型选择 · 连接测试 |
| Anthropic (Claude) | ✅ 密钥存储 · 模型选择 · 连接测试 |
| Google AI (Gemini) | ✅ 密钥存储 · 模型选择 · 连接测试 |
| DeepSeek | ✅ 密钥存储 · 模型选择 · 连接测试 |
| 智谱 AI | ✅ 密钥存储 · 模型选择 · 连接测试 |
| Moonshot | ✅ 密钥存储 · 模型选择 · 连接测试 |
| 百度文心 | ✅ 密钥存储 · 模型选择 |
| 阿里通义 | ✅ 密钥存储 · 模型选择 |
| Azure OpenAI | ✅ 密钥存储 · 模型选择 |
| 自定义服务商 | ✅ 支持 OpenAI 兼容格式 |

### 🤖 模型预设

- 预设各平台常用模型 ID
- 分类标签：对话、代码、长文本、多模态、经济
- 一键复制模型 ID，无需记忆

### ✅ 连接测试

- 添加密钥时一键验证有效性
- 实时反馈密钥状态

### 🔒 安全特性

- **TOTP 双因素认证**：支持 Google Authenticator 等
- **登录保护**：多次失败自动锁定
- **操作日志**：完���的审计追踪
- **速率限制**：防止暴力攻击

---

## 项目结构

```
api-manager/
├── backend/           # FastAPI 后端
│   ├── routers/       # API 路由
│   ├── models.py      # 数据模型
│   ├── schemas.py     # Pydantic 模型
│   ├── auth.py        # 认证逻辑
│   └── config.py      # 配置管理
├── sql/               # 数据库迁移脚本
├── css/               # 样式文件
├── js/                # 前端脚本
├── *.html             # 前端页面
├── docker-compose.yml
├── Dockerfile
└── LICENSE
```

---

## 开发

### 本地开发

```bash
# 安装开发依赖
pip install -r backend/requirements.txt

# 运行开发服务器
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 数据库迁移

```bash
# 创建数据库表
psql -d api_manager -f sql/create_tables.sql

# 添加会员功能
psql -d api_manager -f sql/migrate_add_membership_tier.sql
```

---

## 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 常见问题

### Q: 密钥安全吗？

**A:** 采用 AES-256 加密存储，密钥永不明文显示。即使是管理员也无法查看你的密钥原文。

### Q: 你们会使用我的 API 密钥吗？

**A:** 不会。只负责安全存储，不会调用你的密钥。测试连接功能由浏览器直接请求服务商 API。

### Q: 自托管和托管服务有什么区别？

**A:** 功能完全一致。托管服务省去运维成本，自托管则完全掌控数据。

### Q: 如何从托管服务迁移到自托管？

**A:** 导出数据后导入自托管实例即可。我们的数据格式完全开放。

---

## 技术支持

- 📧 邮箱：ikunfydeos@163.com
- 🐛 提交 Issue：[GitHub Issues](https://github.com/<your-username>/api-key-manager/issues)

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

你可以自由地：
- ✅ 商业使用
- ✅ 修改代码
- ✅ 分发副本
- ✅ 私有使用

唯一要求：保留版权声明。

---

<p align="center">
  <strong>如果这个项目对你有帮助，请给一个 ⭐️ Star 支持！</strong>
</p>
