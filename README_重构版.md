# API密钥管理系统 - 重构版

## 项目概述

这是重构后的API密钥管理系统，主要改进包括：

- ✅ 移除管理员服务，实现纯用户自助服务模式
- ✅ 注册时强制进行TOTP认证
- ✅ 增强用户功能模块（日志、IP记录、余额管理等）
- ✅ 优化数据库结构，确保SQLite兼容性

## 系统架构

### 技术栈
- **后端**: Python 3.13 + FastAPI 0.115.0
- **数据库**: SQLite (支持PostgreSQL)
- **认证**: JWT + TOTP双因素认证
- **前端**: 原生HTML/CSS/JavaScript

### 架构特点
- 前后端分离架构
- RESTful API设计
- 完整的用户认证流程
- 企业级安全防护

## 快速开始

### 环境要求
- Python 3.13+
- pip包管理器

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd api-manager
```

2. **安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

3. **启动服务**
```bash
python run_server.py
```

服务将在 `http://localhost:8000` 启动

### 使用Docker（推荐）

1. **构建镜像**
```bash
docker-compose build
```

2. **启动服务**
```bash
docker-compose up -d
```

## 核心功能

### 1. 用户认证系统

#### 注册流程
1. 访问注册页面
2. 填写用户名、邮箱和密码
3. 系统自动启用TOTP认证
4. 完成注册并跳转到登录页面

#### 登录流程
1. 访问登录页面
2. 输入用户名和密码
3. 输入TOTP令牌
4. 完成登录并进入系统

### 2. 用户自助服务

#### 余额管理
- 查看各服务商余额
- 查看余额变动历史
- 发起会员续费

#### 使用统计
- Token使用统计
- API调用历史
- 按模型/服务商分类统计

#### 安全设置
- TOTP管理
- IP记录查看
- 登录历史

#### 操作日志
- 查看操作记录
- 筛选日志类型
- 查看IP地址信息

### 3. 数据库特性

#### SQLite支持
- 完全兼容SQLite数据库
- 自动创建和迁移数据库结构
- 无需额外配置

#### 数据安全
- API密钥加密存储
- 密码哈希处理
- 完整的操作日志

## API文档

### 认证相关
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录
- `GET /api/totp/secret` - 获取TOTP密钥
- `POST /api/totp/enable` - 启用TOTP
- `POST /api/totp/disable` - 禁用TOTP

### 用户管理
- `GET /api/me` - 获取当前用户信息
- `POST /api/logout` - 用户登出

### 余额管理
- `GET /api/balance` - 获取用户余额
- `POST /api/balance/renew` - 续费会员

### 使用统计
- `GET /api/usage/statistics` - 获取使用统计
- `GET /api/usage/history` - 获取使用历史

### 安全功能
- `GET /api/security/ip-records` - 获取IP记录
- `GET /api/security/login-history` - 获取登录历史

### 日志查看
- `GET /api/logs` - 获取操作日志

## 配置说明

### 环境变量

在生产环境中，建议使用环境变量配置敏感信息：

```bash
# 数据库配置
DATABASE_URL=postgresql://user:pass@host:5432/db

# 安全配置
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
ENCRYPTION_SALT=your-encryption-salt-here

# CORS配置
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 其他配置
ENV=production
RATE_LIMIT_PER_MINUTE=60
```

### 开发环境配置

开发环境使用SQLite，无需额外配置。系统会自动创建数据库文件。

## 测试

### 运行测试脚本
```bash
cd api-manager
python test_refactored_system.py
```

### 测试内容
- 数据库连接测试
- 数据库表结构验证
- 用户注册功能测试
- 余额管理功能测试
- API使用追踪测试
- 续费功能测试
- TOTP功能测试

## 部署指南

### 生产环境部署

1. **准备服务器**
   - 安装Python 3.13+
   - 安装Docker和Docker Compose

2. **配置环境变量**
   ```bash
   export DATABASE_URL=postgresql://user:pass@host:5432/db
   export SECRET_KEY=your-production-secret-key
   export ENCRYPTION_KEY=your-production-encryption-key
   ```

3. **构建和启动**
   ```bash
   docker-compose -f docker-compose.yml up -d --build
   ```

4. **配置反向代理**
   使用Nginx配置反向代理，端口转发到后端服务

### 备份策略

1. **数据库备份**
   ```bash
   docker-compose exec db pg_dump -U postgres llm_api_manager > backup.sql
   ```

2. **配置备份**
   - 备份 `.env` 文件
   - 备份 `nginx.conf` 配置

## 故障排除

### 常见问题

#### 1. 数据库连接失败
- 检查数据库服务是否运行
- 验证连接字符串配置
- 检查网络连接

#### 2. TOTP验证失败
- 确认TOTP密钥正确
- 检查时间同步
- 验证令牌输入格式

#### 3. 前端页面无法加载
- 检查后端服务是否运行
- 验证API响应
- 检查浏览器控制台错误

### 日志查看

#### 后端日志
```bash
docker-compose logs backend
```

#### Nginx日志
```bash
docker-compose logs frontend
```

## 安全建议

### 生产环境安全
1. **使用HTTPS**
   - 配置SSL证书
   - 强制HTTPS访问

2. **定期更新**
   - 更新依赖包
   - 应用安全补丁

3. **访问控制**
   - 配置防火墙规则
   - 限制API访问频率

4. **监控告警**
   - 配置日志监控
   - 设置异常告警

### 数据安全
1. **密钥管理**
   - 定期轮换密钥
   - 安全存储密钥

2. **数据备份**
   - 定期备份数据
   - 测试恢复流程

## 性能优化

### 数据库优化
- 添加适当的索引
- 优化查询语句
- 定期清理日志

### 应用优化
- 使用连接池
- 缓存常用数据
- 压缩静态资源

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件
- 联系团队

---

**注意**: 本重构版系统已完全兼容SQLite，无需额外配置即可运行。建议在生产环境中使用PostgreSQL以获得更好的性能和可靠性。