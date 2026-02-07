# 站内信与即时通讯系统

基于 FastAPI 实现的站内信系统，提供完整的用户认证和站内信管理功能。

## 功能特性

### 已实现
- ✅ 用户认证系统（JWT Token）
  - 用户注册/登录
  - Access Token + Refresh Token 机制
  - 密码加密（bcrypt）
- ✅ 站内信系统
  - 创建站内信（支持多种类型：系统、业务、提醒、公告）
  - 发送站内信（指定用户/全体用户）
  - 站内信列表（分页、筛选）
  - 标记已读/全部标记已读
  - 删除站内信（软删除）
  - 未读数量统计
- ✅ 管理端 API
  - 站内信内容管理
  - 批量发送站内信

### 计划中（未来版本）
- ⏳ WebSocket 实时推送
- ⏳ 即时通讯（IM）功能
- ⏳ 好友关系管理
- ⏳ 消息模板系统
- ⏳ 用户偏好设置

## 技术栈

- **Web 框架**: FastAPI 0.115.0
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy 2.0.35
- **数据库迁移**: Alembic 1.13.3
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt
- **数据验证**: Pydantic 2.9.2
- **测试框架**: pytest

## 项目结构

```
inbox_and_im/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 应用入口
│   ├── config.py                   # 配置文件
│   ├── dependencies.py             # 依赖注入
│   │
│   ├── core/                       # 核心功能
│   │   ├── security.py             # JWT、密码加密
│   │   └── database.py             # 数据库连接
│   │
│   ├── models/                     # SQLAlchemy 模型
│   │   ├── user.py                 # 用户模型
│   │   └── notification.py         # 站内信模型
│   │
│   ├── schemas/                    # Pydantic Schema
│   │   ├── user.py                 # 用户 Schema
│   │   └── notification.py         # 站内信 Schema
│   │
│   ├── api/                        # API 路由
│   │   ├── v1/
│   │   │   ├── auth.py             # 认证 API
│   │   │   ├── notifications.py    # 站内信 API（用户端）
│   │   │   └── admin/
│   │   │       └── notifications.py  # 站内信管理 API（管理端）
│   │
│   ├── services/                   # 业务逻辑层
│   │   ├── auth_service.py         # 认证服务
│   │   └── notification_service.py # 站内信服务
│   │
│   └── middleware/                 # 中间件
│
├── alembic/                        # 数据库迁移
│   └── versions/
│
├── tests/                          # 测试代码
├── docs/                           # 文档
├── .env.example                    # 环境变量示例
├── .gitignore
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- PostgreSQL 12+

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

主要配置项：

```env
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/inbox_im

# JWT 密钥（生产环境必须更改）
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars

# Token 有效期
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 4. 初始化数据库

```bash
# 创建数据库
createdb inbox_im

# 运行数据库迁移
alembic upgrade head
```

### 5. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. 访问 API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 认证 API

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/auth/refresh` | 刷新 Token |
| GET | `/api/v1/auth/me` | 获取当前用户信息 |

### 站内信 API（用户端）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/notifications` | 获取站内信列表 |
| GET | `/api/v1/notifications/unread-count` | 获取未读数量 |
| GET | `/api/v1/notifications/{id}` | 获取站内信详情 |
| POST | `/api/v1/notifications/{id}/read` | 标记已读 |
| POST | `/api/v1/notifications/read-all` | 全部标记已读 |
| DELETE | `/api/v1/notifications/{id}` | 删除站内信 |

### 站内信管理 API（管理端）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/admin/notifications` | 创建站内信 |
| GET | `/api/v1/admin/notifications` | 站内信管理列表 |
| GET | `/api/v1/admin/notifications/{id}` | 获取站内信详情 |
| PUT | `/api/v1/admin/notifications/{id}` | 更新站内信 |
| DELETE | `/api/v1/admin/notifications/{id}` | 删除站内信 |
| POST | `/api/v1/admin/notifications/{id}/send` | 发送站内信给用户 |

## 使用示例

### 1. 用户注册

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

返回：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. 创建站内信（管理端）

```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "system",
    "title": "系统通知",
    "content": "这是一条系统通知",
    "priority": 0
  }'
```

### 4. 发送站内信给用户

```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/<notification_id>/send" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["user-uuid-1", "user-uuid-2"],
    "send_to_all": false
  }'
```

### 5. 获取站内信列表

```bash
curl -X GET "http://localhost:8000/api/v1/notifications?page=1&page_size=20" \
  -H "Authorization: Bearer <access_token>"
```

### 6. 标记站内信为已读

```bash
curl -X POST "http://localhost:8000/api/v1/notifications/<record_id>/read" \
  -H "Authorization: Bearer <access_token>"
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_auth.py

# 查看测试覆盖率
pytest --cov=app --cov-report=html
```

## 数据库设计

### 用户表 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名（唯一） |
| email | VARCHAR(100) | 邮箱（唯一） |
| password_hash | VARCHAR(255) | 密码哈希 |
| avatar_url | VARCHAR(500) | 头像 URL |
| status | ENUM | 用户状态（online/offline/away/busy） |
| last_login_at | TIMESTAMP | 最后登录时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 站内信内容表 (notifications)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| type | VARCHAR(50) | 站内信类型 |
| title | VARCHAR(200) | 标题 |
| content | TEXT | 内容 |
| action_url | VARCHAR(500) | 点击跳转链接 |
| priority | INTEGER | 优先级（0:普通 1:重要 2:紧急） |
| created_by | UUID | 创建者 ID |
| created_at | TIMESTAMP | 创建时间 |
| expires_at | TIMESTAMP | 过期时间 |

### 站内信用户记录表 (notification_records)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| notification_id | UUID | 站内信 ID |
| user_id | UUID | 用户 ID |
| is_read | BOOLEAN | 是否已读 |
| read_at | TIMESTAMP | 阅读时间 |
| is_deleted | BOOLEAN | 是否已删除 |
| deleted_at | TIMESTAMP | 删除时间 |
| created_at | TIMESTAMP | 创建时间 |

## 站内信类型

- **system**: 系统通知
- **business**: 业务通知
- **reminder**: 提醒通知
- **announcement**: 公告

## 安全性

- 密码使用 bcrypt 加密（salt rounds = 12）
- JWT Token 签名使用 HS256 算法
- Access Token 有效期 15 分钟
- Refresh Token 有效期 7 天
- 支持 Token 刷新机制
- CORS 配置限制跨域访问

## 性能优化

- 数据库连接池（pool_size=5, max_overflow=10）
- 索引优化（user_id, notification_id, is_read, created_at）
- 分页查询（避免一次性加载大量数据）
- 内容与记录分离设计（避免数据冗余）

## 后续扩展

- [ ] WebSocket 实时推送
- [ ] Redis 缓存（未读数量、用户偏好）
- [ ] 消息队列（Celery/RabbitMQ）异步发送
- [ ] 消息模板系统
- [ ] 用户偏好设置
- [ ] 即时通讯功能
- [ ] 好友关系管理

## 参考文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [JWT 最佳实践](https://jwt.io/introduction)

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。
