# API Key Manager

<p align="center">
  <img src="api-manager-new-color.png" alt="API Key Manager" width="400">
</p>

<p align="center">
  <strong>🔐 All-in-One API Key Management Platform</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI"></a>
  <img src="https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-orange" alt="Database">
</p>

<p align="center">
  <strong>⚡ Deploy in 3 Minutes</strong> · No Database Required · Ready to Use
</p>

<p align="center">
  <a href="README.md">简体中文</a> | <strong>English</strong>
</p>

---

## ✨ Features

- 🚀 **Quick Deploy** — One-click install script, no manual configuration
- 💾 **Zero Dependencies** — SQLite by default, no database installation needed
- 🔐 **Bank-Grade Encryption** — AES-256 encrypted storage, keys never in plain text
- 🏷️ **Pre-configured Providers** — Supports OpenAI, Claude, Gemini, DeepSeek and 10+ platforms
- 🔒 **Two-Factor Authentication** — TOTP support via Google Authenticator
- 📱 **Responsive Design** — Works on mobile, tablet, and desktop

---

## ⚡ Quick Start

### Windows

```powershell
# 1. Clone the repository
git clone https://github.com/ikunfydeos-tech/APIKey.git
cd APIKey

# 2. Run install script (Right-click -> Run with PowerShell)
.\install.ps1

# 3. Start the server
.\start.ps1

# 4. Open http://localhost:8000
```

### Linux / Mac

```bash
# 1. Clone the repository
git clone https://github.com/ikunfydeos-tech/APIKey.git
cd APIKey

# 2. Run install script
chmod +x install.sh && ./install.sh

# 3. Start the server
./start.sh

# 4. Open http://localhost:8000
```

### Docker (SQLite - Recommended for Personal Use)

```bash
# Quick start with SQLite (easiest)
docker-compose -f docker-compose.sqlite.yml up -d

# Access at http://localhost:8000
```

### Docker (PostgreSQL - Recommended for Production)

```bash
# Create .env file first
cp .env.example .env
# Edit .env and set required values:
# - SECRET_KEY (at least 32 characters)
# - ENCRYPTION_KEY (32 bytes)
# - ENCRYPTION_SALT (16 bytes)
# - DB_PASSWORD (PostgreSQL password)

# Start with PostgreSQL
docker-compose up -d

# Access at http://localhost:8000
```

---

## 🗄️ Database Options

| Database | Use Case | Docker Command |
|----------|----------|----------------|
| **SQLite** | Personal, Testing, Development | `docker-compose -f docker-compose.sqlite.yml up -d` |
| **PostgreSQL** | Production, Multi-user, High-traffic | `docker-compose up -d` |

**SQLite is the default** — No additional setup required.

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection | SQLite (dev) / PostgreSQL (prod) |
| `SECRET_KEY` | JWT secret key | Auto-generated |
| `ENCRYPTION_KEY` | AES encryption key | Auto-generated |
| `ENCRYPTION_SALT` | Encryption salt | Auto-generated |
| `CORS_ORIGINS` | Allowed origins | `*` |

### Switch to PostgreSQL (Production)

```bash
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/api_manager

# Install PostgreSQL driver
pip install psycopg[binary]
```

---

## 🎯 Core Features

### 🔐 Secure Encrypted Storage

- **AES-256 Encryption** — Bank-grade encryption for all API keys
- **Key Preview** — Only shows `sk-abc...xyz`, never plain text
- **One-Click Copy** — Use and go, no traces left

### 🏷️ Built-in Providers

| Provider | Key Storage | Model Selection | Connection Test |
|----------|:-----------:|:---------------:|:---------------:|
| OpenAI | ✅ | ✅ | ✅ |
| Anthropic (Claude) | ✅ | ✅ | ✅ |
| Google AI (Gemini) | ✅ | ✅ | ✅ |
| DeepSeek | ✅ | ✅ | ✅ |
| Zhipu AI | ✅ | ✅ | ✅ |
| Moonshot | ✅ | ✅ | ✅ |
| Baidu Wenxin | ✅ | ✅ | - |
| Alibaba Tongyi | ✅ | ✅ | - |
| Azure OpenAI | ✅ | ✅ | - |
| Custom Provider | ✅ | ✅ | ✅ |

### 🔒 Security Features

- **TOTP Two-Factor Auth** — Google Authenticator support
- **Login Protection** — Auto-lock after multiple failures
- **Audit Logs** — Complete operation tracking
- **Rate Limiting** — Brute-force attack prevention

---

## 📁 Project Structure

```
APIKey/
├── backend/              # Backend service
│   ├── routers/          # API routes
│   ├── models.py         # Data models
│   ├── config.py         # Configuration
│   └── database.py       # Database connection
├── css/                  # Stylesheets
├── js/                   # Frontend scripts
├── *.html                # Pages
├── install.ps1           # Windows install script
├── install.sh            # Linux/Mac install script
├── start.ps1             # Windows start script
├── start.sh              # Linux/Mac start script
├── docker-compose.yml    # Docker config (PostgreSQL)
├── docker-compose.sqlite.yml  # Docker config (SQLite)
└── LICENSE               # MIT License
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI |
| Database | SQLite / PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | JWT + TOTP |
| Encryption | AES-256 |
| Frontend | Vanilla HTML/CSS/JS |

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📋 FAQ

### Q: What database does it use by default?

**A:** SQLite by default — no database installation required. PostgreSQL is recommended for production.

### Q: Are my API keys safe?

**A:** Yes! Keys are encrypted with AES-256 and never stored in plain text. Even administrators cannot view your original keys.

### Q: Can I add custom providers?

**A:** Yes! Custom providers with OpenAI-compatible API format are supported.

### Q: How do I backup my data?

**A:** For SQLite, simply copy the `api_manager.db` file. For PostgreSQL, use `pg_dump`.

---

## 📄 License

[MIT License](LICENSE) — Free for commercial use, modification, and distribution.

---

## 📧 Contact

- 🐛 Issues: [GitHub Issues](https://github.com/ikunfydeos-tech/APIKey/issues)
- 📧 Email: ikunfydeos@163.com

---

<p align="center">
  <strong>If this project helps you, please give it a ⭐️ Star!</strong>
</p>
