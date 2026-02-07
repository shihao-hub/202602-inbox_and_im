# 快速启动指南

## 前置条件

1. **Python**: 3.10 或更高版本
2. **PostgreSQL**: 12 或更高版本
3. **Git**: 用于克隆项目（可选）

## 安装步骤

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

### 2. 配置数据库

#### 创建数据库

```bash
# 方式一：使用 createdb 命令
createdb inbox_im

# 方式二：使用 psql
psql -U postgres
CREATE DATABASE inbox_im;
\q
```

#### 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，修改数据库连接信息：

```env
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/inbox_im
SECRET_KEY=你的密钥（至少32位随机字符串）
```

### 3. 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head
```

### 4. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或者使用更详细的日志
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 5. 访问应用

- **API 文档 (Swagger)**: http://localhost:8000/docs
- **API 文档 (ReDoc)**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 快速测试

### 1. 注册用户

使用 Swagger UI (http://localhost:8000/docs) 或 curl：

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. 登录

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
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### 3. 创建站内信（管理员）

```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications" \
  -H "Authorization: Bearer <你的access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "system",
    "title": "欢迎通知",
    "content": "欢迎使用站内信系统！",
    "priority": 0
  }'
```

返回：

```json
{
  "id": "通知ID",
  "type": "system",
  "title": "欢迎通知",
  ...
}
```

### 4. 发送站内信给用户

```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/<通知ID>/send" \
  -H "Authorization: Bearer <你的access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["<用户ID>"],
    "send_to_all": false
  }'
```

### 5. 查看站内信

```bash
curl -X GET "http://localhost:8000/api/v1/notifications" \
  -H "Authorization: Bearer <你的access_token>"
```

## 常见问题

### 问题 1: 数据库连接失败

**错误信息**: `psycopg2.OperationalError: connection to server at "localhost" failed`

**解决方案**:
1. 检查 PostgreSQL 服务是否运行
2. 检查 `.env` 中的数据库连接信息是否正确
3. 确认数据库已创建

### 问题 2: 模块导入错误

**错误信息**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
1. 确认虚拟环境已激活
2. 重新安装依赖：`pip install -r requirements.txt`

### 问题 3: Alembic 迁移失败

**错误信息**: `Target database is not up to date`

**解决方案**:
1. 查看当前版本：`alembic current`
2. 查看迁移历史：`alembic history`
3. 重置数据库（谨慎使用）：
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

### 问题 4: Token 验证失败

**错误信息**: `Invalid token`

**解决方案**:
1. 检查 Token 是否过期（Access Token 有效期 15 分钟）
2. 使用 Refresh Token 刷新：`POST /api/v1/auth/refresh`
3. 重新登录获取新 Token

## 开发工具

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_auth.py

# 查看详细输出
pytest -v

# 查看测试覆盖率
pytest --cov=app --cov-report=html
```

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 升级到最新版本
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

### 查看日志

开发模式下，日志会直接输出到控制台。

生产环境建议使用日志文件：

```bash
# 启动时重定向日志
uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/app.log 2>&1
```

## 生产环境部署

### 使用 Docker（推荐）

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 使用 Gunicorn

```bash
pip install gunicorn

gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用 Supervisor

```ini
[program:inbox_im]
command=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/path/to/inbox_and_im
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/inbox_im.err.log
stdout_logfile=/var/log/inbox_im.out.log
```

## 性能优化建议

1. **数据库连接池**: 已配置连接池（pool_size=5, max_overflow=10）
2. **缓存**: 考虑使用 Redis 缓存未读数量
3. **异步任务**: 大批量发送站内信使用消息队列（Celery）
4. **负载均衡**: 使用 Nginx 反向代理

## 监控和维护

### 日志监控

- 应用日志：访问日志、错误日志
- 数据库日志：慢查询日志
- 系统监控：CPU、内存、磁盘使用率

### 数据备份

```bash
# 备份数据库
pg_dump -U postgres inbox_im > backup_$(date +%Y%m%d).sql

# 恢复数据库
psql -U postgres inbox_im < backup_20250207.sql
```

### 定期维护

- 清理过期的站内信记录
- 清理已删除的软删除数据
- 优化数据库索引

## 下一步

- 阅读 [API 文档](./docs/api-documentation.md) 了解所有 API 端点
- 阅读 [数据库设计文档](./docs/database-schema.md) 了解数据库结构
- 阅读 [站内信类型说明](./docs/notification-types.md) 了解站内信分类
- 查看 [README](./README.md) 了解更多功能特性

## 技术支持

如有问题，请：
1. 查看文档
2. 检查日志输出
3. 提交 Issue

---

**祝您使用愉快！** 🎉
