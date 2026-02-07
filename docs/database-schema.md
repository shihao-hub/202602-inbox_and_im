# 数据库设计文档

## 概述

本文档详细描述了站内信与即时通讯系统的数据库设计。

## 技术选型

- **数据库**: PostgreSQL 12+
- **ORM**: SQLAlchemy 2.0
- **迁移工具**: Alembic

## 数据库表设计

### 1. 用户表 (users)

存储用户基本信息和认证数据。

#### 表结构

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | 用户 ID |
| username | VARCHAR(50) | NOT NULL, UNIQUE | - | 用户名 |
| email | VARCHAR(100) | NOT NULL, UNIQUE | - | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | - | 密码哈希（bcrypt） |
| avatar_url | VARCHAR(500) | NULL | - | 头像 URL |
| status | ENUM | NOT NULL | 'offline' | 用户状态 |
| last_login_at | TIMESTAMP | NULL | - | 最后登录时间 |
| created_at | TIMESTAMP | NOT NULL | now() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | now() | 更新时间 |

#### 索引

- PRIMARY KEY: `id`
- UNIQUE INDEX: `username`
- UNIQUE INDEX: `email`
- INDEX: `id` (用于关联查询)

#### 用户状态枚举 (UserStatus)

| 值 | 说明 |
|----|------|
| online | 在线 |
| offline | 离线 |
| away | 离开 |
| busy | 忙碌 |

#### 关系

- 一对多: `created_by` → `notifications.created_by` (创建的站内信)
- 一对多: `id` → `notification_records.user_id` (站内信记录)

#### 创建 SQL

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'away', 'busy')),
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_id ON users(id);
```

---

### 2. 站内信内容表 (notifications)

存储站内信的模板内容，避免重复存储相同内容。

#### 表结构

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | 站内信 ID |
| type | VARCHAR(50) | NOT NULL | - | 站内信类型 |
| title | VARCHAR(200) | NOT NULL | - | 标题 |
| content | TEXT | NOT NULL | - | 内容 |
| action_url | VARCHAR(500) | NULL | - | 点击跳转链接 |
| priority | INTEGER | NOT NULL | 0 | 优先级 |
| created_by | UUID | FOREIGN KEY | NULL | 创建者 ID |
| created_at | TIMESTAMP | NOT NULL | now() | 创建时间 |
| expires_at | TIMESTAMP | NULL | - | 过期时间 |

#### 索引

- PRIMARY KEY: `id`
- INDEX: `type` (用于按类型筛选)
- INDEX: `id` (用于关联查询)

#### 站内信类型 (NotificationType)

| 值 | 说明 |
|----|------|
| system | 系统通知 |
| business | 业务通知 |
| reminder | 提醒通知 |
| announcement | 公告 |

#### 优先级 (NotificationPriority)

| 值 | 说明 |
|----|------|
| 0 | 普通 |
| 1 | 重要 |
| 2 | 紧急 |

#### 关系

- 多对一: `created_by` → `users.id` (创建者)
- 一对多: `id` → `notification_records.notification_id` (站内信记录)

#### 创建 SQL

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    action_url VARCHAR(500),
    priority INTEGER DEFAULT 0 NOT NULL CHECK (priority IN (0, 1, 2)),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP
);

CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_id ON notifications(id);
```

---

### 3. 站内信用户记录表 (notification_records)

记录每个用户收到的站内信及状态。

#### 表结构

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | 记录 ID |
| notification_id | UUID | FOREIGN KEY | NOT NULL | 站内信 ID |
| user_id | UUID | FOREIGN KEY | NOT NULL | 用户 ID |
| is_read | BOOLEAN | NOT NULL | FALSE | 是否已读 |
| read_at | TIMESTAMP | NULL | - | 阅读时间 |
| is_deleted | BOOLEAN | NOT NULL | FALSE | 是否已删除 |
| deleted_at | TIMESTAMP | NULL | - | 删除时间 |
| created_at | TIMESTAMP | NOT NULL | now() | 创建时间 |

#### 唯一约束

- UNIQUE (`notification_id`, `user_id`) - 一个用户只能收到一次同一条站内信

#### 索引

- PRIMARY KEY: `id`
- INDEX: `notification_id` (用于关联查询站内信内容)
- INDEX: `user_id` (用于查询用户的站内信)
- 复合索引建议: `(user_id, is_read, created_at)` (用于查询用户未读站内信)

#### 关系

- 多对一: `notification_id` → `notifications.id` (站内信内容)
- 多对一: `user_id` → `users.id` (用户)

#### 创建 SQL

```sql
CREATE TABLE notification_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(notification_id, user_id)
);

CREATE INDEX idx_notification_records_notification_id ON notification_records(notification_id);
CREATE INDEX idx_notification_records_user_id ON notification_records(user_id);
CREATE INDEX idx_notification_records_id ON notification_records(id);

-- 性能优化索引（可选）
CREATE INDEX idx_notification_records_user_unread ON notification_records(user_id, is_read, created_at) WHERE is_deleted = FALSE;
```

---

## ER 图

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────────┐
│   users     │         │ notifications│         │ notification_records│
├─────────────┤         ├──────────────┤         ├─────────────────────┤
│ id (PK)     │──┐    ┌─│ id (PK)      │──┐    ┌─│ id (PK)             │
│ username    │  │    │ │ type         │  │    │ │ notification_id (FK)│
│ email       │  │    │ │ title        │  │    │ │ user_id (FK)        │
│ password... │  │    │ │ content      │  │    │ │ is_read             │
│ status      │  │    │ │ priority     │  │    │ │ read_at             │
│ ...         │  │    │ │ created_by(FK)│  │    │ │ is_deleted          │
└─────────────┘  │    │ └──────────────┘  │    │ └─────────────────────┘
                  │    │                   │
                  │    └───────────────────┘
                  │
                  └─────────────────────────┘
```

---

## 数据库设计原则

### 1. 内容与记录分离

将站内信内容（`notifications`）和用户记录（`notification_records`）分开存储：

**优点**:
- 避免数据冗余（相同内容只存储一次）
- 便于修改站内信内容（不影响已发送的记录）
- 节省存储空间

**缺点**:
- 需要关联查询（性能影响较小，有索引优化）

### 2. 软删除

用户删除站内信时使用软删除（标记 `is_deleted=True`）而非物理删除：

**优点**:
- 数据可恢复
- 保留审计日志
- 可用于统计分析

**缺点**:
- 需要定期清理历史数据
- 查询时需要过滤已删除数据

### 3. 级联删除

- 删除站内信内容时，自动删除所有用户的站内信记录（`ON DELETE CASCADE`）
- 删除用户时，自动删除该用户的所有站内信记录

### 4. 索引优化

主要查询场景：
- 按用户查询站内信（`user_id`）
- 按类型筛选站内信（`type`）
- 按已读/未读筛选（`is_read`）
- 按时间排序（`created_at`）

索引设计：
- 所有外键字段建立索引
- 常用查询字段建立索引
- 复合索引用于复杂查询

---

## 性能优化建议

### 1. 数据库连接池

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # 连接池大小
    max_overflow=10,      # 最大溢出连接数
    pool_pre_ping=True,   # 检查连接有效性
)
```

### 2. 查询优化

**避免 N+1 查询**:

```python
# 不推荐
records = db.query(NotificationRecord).all()
for record in records:
    print(record.notification.title)  # N+1 查询

# 推荐
records = (
    db.query(NotificationRecord)
    .options(joinedload(NotificationRecord.notification))
    .all()
)
```

**使用分页**:

```python
query = db.query(NotificationRecord).filter(NotificationRecord.user_id == user_id)
total = query.count()
items = query.offset(skip).limit(limit).all()
```

### 3. 缓存策略（未来扩展）

- Redis 缓存未读数量
- Redis 缓存用户偏好设置
- 查询结果缓存（短期）

---

## 数据迁移

### 创建迁移

```bash
alembic revision --autogenerate -m "描述"
```

### 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade +1

# 降级
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

---

## 备份与恢复

### 备份

```bash
# 备份整个数据库
pg_dump -U postgres inbox_im > backup.sql

# 仅备份数据
pg_dump -U postgres --data-only inbox_im > data.sql

# 仅备份结构
pg_dump -U postgres --schema-only inbox_im > schema.sql
```

### 恢复

```bash
psql -U postgres inbox_im < backup.sql
```

---

## 监控指标

建议监控以下数据库指标：

1. **性能指标**
   - 查询响应时间
   - 慢查询日志
   - 连接池使用率

2. **存储指标**
   - 表大小增长
   - 索引大小
   - 磁盘使用率

3. **业务指标**
   - 站内信发送量
   - 用户活跃度
   - 未读站内信数量分布

---

## 未来扩展

### 即时通讯功能（IM）

需要添加以下表：

1. **好友关系表** (friendships)
2. **聊天消息表** (chat_messages)
3. **群组表** (groups)
4. **群组成员表** (group_members)

### WebSocket 连接管理

使用 Redis 存储在线状态和连接信息：

```
Key: online:users
Value: Set of user_ids

Key: user:connections:{user_id}
Value: List of connection_ids
```

---

## 相关文档

- [API 文档](./api-documentation.md)
- [站内信类型说明](./notification-types.md)
- [README](../README.md)
