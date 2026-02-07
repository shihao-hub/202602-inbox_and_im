# 站内信系统实现原理详解

## 📊 站内信系统架构概览

```
┌─────────────────────────────────────────────────────────┐
│                     客户端 (浏览器/App)                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI 应用层                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  认证中间件   │  │   API 路由    │  │   权限验证    │ │
│  │  (JWT Token) │  │  (REST API)  │  │  (依赖注入)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   业务逻辑层 (Services)                  │
│  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │   AuthService        │  │ NotificationService  │   │
│  │  - register          │  │  - 创建站内信         │   │
│  │  - login             │  │  - 发送给用户         │   │
│  │  - verify_token      │  │  - 查询列表           │   │
│  └──────────────────────┘  │  - 标记已读           │   │
│                            │  - 删除站内信         │   │
│                            └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   数据访问层 (ORM - SQLAlchemy)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ User Model   │  │ Notification │  │ Notification │ │
│  │              │  │   Model      │  │   Record     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   PostgreSQL 数据库                      │
└─────────────────────────────────────────────────────────┘
```

## 🎯 核心设计思想：内容与记录分离

站内信系统最重要的设计是**内容与记录分离**：

```
┌────────────────────┐         ┌──────────────────────────┐
│  notifications     │         │  notification_records    │
│  (站内信内容)       │         │  (用户接收记录)           │
├────────────────────┤         ├──────────────────────────┤
│ id: msg_001        │────┬────│ id: record_001           │
│ title: "系统公告"  │    │    │ notification_id: msg_001 │
│ content: "..."     │    ├────│ user_id: user_A          │
│                    │    │    │ is_read: false           │
└────────────────────┘    │    └──────────────────────────┘
                          │
                          ├────┌──────────────────────────┐
                          │    │ id: record_002           │
                          └────│ notification_id: msg_001 │
                               │ user_id: user_B          │
                               │ is_read: true            │
                               └──────────────────────────┘
```

**为什么要这样设计？**

1. **避免数据冗余**：1000个用户收到同一条公告，不需要存储1000份相同的内容
2. **便于修改**：修改公告内容时，只需要更新一次
3. **节省存储空间**：内容只存一份，用户只存记录

## 📦 数据模型实现

站内信系统由三个核心模型组成：

### 1. 用户表 (users)

```python
class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.OFFLINE)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    notification_records = relationship("NotificationRecord", back_populates="user", cascade="all, delete-orphan")
```

### 2. 站内信内容表 (notifications)

```python
class Notification(Base):
    """站内信内容表"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(String(50), nullable=False, index=True, comment="站内信类型")
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    action_url = Column(String(500), nullable=True, comment="点击跳转链接")
    priority = Column(Integer, default=0, nullable=False, comment="优先级 0:普通 1:重要 2:紧急")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")

    # 关系
    records = relationship("NotificationRecord", back_populates="notification", cascade="all, delete-orphan")
```

**表结构**：

```sql
CREATE TABLE notifications (
    id              UUID PRIMARY KEY,        -- 站内信ID
    type            VARCHAR(50),             -- 类型：system/business/reminder/announcement
    title           VARCHAR(200),            -- 标题
    content         TEXT,                    -- 内容
    action_url      VARCHAR(500),            -- 点击跳转链接
    priority        INTEGER DEFAULT 0,       -- 优先级：0普通/1重要/2紧急
    created_by      UUID,                    -- 创建者ID
    created_at      TIMESTAMP,               -- 创建时间
    expires_at      TIMESTAMP                -- 过期时间（可选）
);
```

**站内信类型**：
- `system`: 系统通知
- `business`: 业务通知
- `reminder`: 提醒通知
- `announcement`: 公告

### 3. 站内信用户记录表 (notification_records)

```python
class NotificationRecord(Base):
    """站内信用户记录表"""
    __tablename__ = "notification_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_read = Column(Boolean, default=False, nullable=False, comment="是否已读")
    read_at = Column(DateTime(timezone=True), nullable=True, comment="阅读时间")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已删除")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 关系
    notification = relationship("Notification", back_populates="records")
    user = relationship("User", back_populates="notification_records")

    # 唯一约束：一个用户只能收到一次同一条站内信
    __table_args__ = (UniqueConstraint("notification_id", "user_id", name="unique_notification_user"),)
```

**表结构**：

```sql
CREATE TABLE notification_records (
    id              UUID PRIMARY KEY,
    notification_id UUID,                    -- 关联站内信内容
    user_id         UUID,                    -- 接收用户
    is_read         BOOLEAN DEFAULT FALSE,   -- 是否已读
    read_at         TIMESTAMP,               -- 阅读时间
    is_deleted      BOOLEAN DEFAULT FALSE,   -- 是否删除（软删除）
    deleted_at      TIMESTAMP,               -- 删除时间
    created_at      TIMESTAMP,               -- 创建时间

    UNIQUE(notification_id, user_id)        -- 唯一约束：防止重复发送
);
```

## 2️⃣ 业务逻辑层

### 📌 创建站内信

```python
@staticmethod
def create_notification(
    db: Session,
    notification_create: NotificationCreate,
    created_by_id: str,
) -> NotificationResponse:
    """
    创建站内信（仅创建内容，不发送给用户）
    """
    notification = Notification(
        type=notification_create.type,
        title=notification_create.title,
        content=notification_create.content,
        action_url=notification_create.action_url,
        priority=notification_create.priority,
        created_by=created_by_id,
        expires_at=notification_create.expires_at,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return NotificationResponse.model_validate(notification)
```

**流程**：
1. 创建 `Notification` 对象
2. 插入到数据库
3. 返回站内信信息（但还未发送给任何用户）

### 📌 发送站内信给用户

```python
@staticmethod
def send_to_users(
    db: Session,
    notification_id: str,
    user_ids: List[str],
) -> int:
    """
    发送站内信给指定用户
    """
    # 1. 验证站内信是否存在
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="站内信不存在")

    # 2. 批量创建用户记录
    records = []
    for user_id in user_ids:
        # 检查是否已存在（防止重复发送）
        existing = db.query(NotificationRecord).filter(
            NotificationRecord.notification_id == notification_id,
            NotificationRecord.user_id == user_id,
        ).first()

        if not existing:  # 不存在才创建
            records.append(NotificationRecord(
                notification_id=notification_id,
                user_id=user_id,
            ))

    # 3. 批量插入数据库（性能优化）
    db.bulk_save_objects(records)
    db.commit()

    return len(records)  # 返回成功发送数量
```

**关键点**：
1. **去重检查**：通过数据库查询防止重复发送
2. **批量插入**：使用 `bulk_save_objects` 提高性能
3. **事务处理**：全部成功或全部失败

### 📌 发送给所有用户

```python
@staticmethod
def send_to_all_users(db: Session, notification_id: str) -> int:
    """
    发送站内信给所有用户
    """
    # 1. 验证站内信是否存在
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="站内信不存在")

    # 2. 获取所有用户 ID
    all_users = db.query(User.id).all()
    user_ids = [str(user.id) for user in all_users]

    # 3. 调用 send_to_users 批量发送
    return NotificationService.send_to_users(db, notification_id, user_ids)
```

### 📌 查询用户的站内信列表

```python
@staticmethod
def get_user_notifications(
    db: Session,
    user_id: str,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> NotificationRecordListResponse:
    """
    获取用户的站内信列表（支持筛选、分页）
    """
    # 1. 构建基础查询
    query = db.query(NotificationRecord)\
        .filter(
            NotificationRecord.user_id == user_id,
            NotificationRecord.is_deleted == False  # 过滤已删除
        )\
        .join(Notification)  # 关联查询站内信内容

    # 2. 动态筛选条件
    if is_read is not None:  # 只查已读/未读
        query = query.filter(NotificationRecord.is_read == is_read)

    if notification_type:  # 按类型筛选
        query = query.filter(Notification.type == notification_type)

    # 3. 排序（最新的在前）
    query = query.order_by(NotificationRecord.created_at.desc())

    # 4. 统计总数和未读数
    total = query.count()

    unread_count = db.query(NotificationRecord).filter(
        NotificationRecord.user_id == user_id,
        NotificationRecord.is_read == False,
        NotificationRecord.is_deleted == False,
    ).count()

    # 5. 分页查询
    records = query.offset(skip).limit(limit).all()

    # 6. 转换为响应格式
    items = [NotificationRecordResponse.model_validate(record) for record in records]

    return NotificationRecordListResponse(
        total=total,
        unread_count=unread_count,
        items=items,
    )
```

**查询流程**：
```
用户A查询站内信列表
    │
    ├─ 查询 notification_records 表（user_id = A, is_deleted = false）
    │
    ├─ 关联 notifications 表（获取标题、内容等）
    │
    ├─ 应用筛选条件（已读/未读、类型）
    │
    ├─ 按时间倒序排序
    │
    └─ 分页返回
```

### 📌 标记已读

```python
@staticmethod
def mark_as_read(db: Session, user_id: str, record_id: str) -> None:
    """
    标记站内信为已读
    """
    # 1. 查询站内信记录（验证权限）
    record = db.query(NotificationRecord).filter(
        NotificationRecord.id == record_id,
        NotificationRecord.user_id == user_id,  # 验证是否是自己的站内信
        NotificationRecord.is_deleted == False,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="站内信不存在")

    # 2. 更新已读状态（只在未读时更新）
    if not record.is_read:
        record.is_read = True
        record.read_at = datetime.utcnow()  # 记录阅读时间
        db.commit()

@staticmethod
def mark_all_as_read(db: Session, user_id: str) -> int:
    """
    标记所有站内信为已读
    """
    # 1. 查询所有未读站内信
    unread_records = db.query(NotificationRecord).filter(
        NotificationRecord.user_id == user_id,
        NotificationRecord.is_read == False,
        NotificationRecord.is_deleted == False,
    ).all()

    # 2. 批量更新
    count = 0
    for record in unread_records:
        record.is_read = True
        record.read_at = datetime.utcnow()
        count += 1

    db.commit()
    return count  # 返回标记数量
```

### 📌 软删除

```python
@staticmethod
def delete_notification_record(db: Session, user_id: str, record_id: str) -> None:
    """
    删除站内信（软删除）
    """
    record = db.query(NotificationRecord).filter(
        NotificationRecord.id == record_id,
        NotificationRecord.user_id == user_id,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="站内信不存在")

    # 软删除：只标记，不物理删除
    record.is_deleted = True
    record.deleted_at = datetime.utcnow()
    db.commit()
```

## 3️⃣ API 层实现

### 用户端 API

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("", response_model=NotificationRecordListResponse)
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="筛选已读/未读"),
    notification_type: Optional[str] = Query(None, description="站内信类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),  # JWT 认证
    db: Session = Depends(get_db),
):
    """
    获取当前用户的站内信列表
    """
    skip = (page - 1) * page_size
    return NotificationService.get_user_notifications(
        db,
        user_id=str(current_user.id),
        is_read=is_read,
        notification_type=notification_type,
        skip=skip,
        limit=page_size,
    )

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取未读站内信数量"""
    count = NotificationService.get_unread_count(db, str(current_user.id))
    return {"unread_count": count}

@router.post("/{record_id}/read", status_code=204)
async def mark_notification_as_read(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记站内信为已读"""
    NotificationService.mark_as_read(db, str(current_user.id), record_id)
    return None

@router.post("/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """全部标记已读"""
    count = NotificationService.mark_all_as_read(db, str(current_user.id))
    return {"message": f"已将 {count} 条站内信标记为已读"}

@router.delete("/{record_id}", status_code=204)
async def delete_notification(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除站内信（软删除）"""
    NotificationService.delete_notification_record(db, str(current_user.id), record_id)
    return None
```

### 管理端 API

```python
admin_router = APIRouter()

@admin_router.post("/notifications", response_model=NotificationResponse, status_code=201)
async def create_notification(
    notification_create: NotificationCreate,
    current_user: User = Depends(require_admin),  # 需要管理员权限
    db: Session = Depends(get_db),
):
    """创建站内信"""
    return NotificationService.create_notification(
        db,
        notification_create,
        created_by_id=str(current_user.id),
    )

@admin_router.post("/notifications/{notification_id}/send")
async def send_notification(
    notification_id: str,
    send_request: NotificationSendRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """发送站内信给用户"""
    if send_request.send_to_all:
        count = NotificationService.send_to_all_users(db, notification_id)
    else:
        count = NotificationService.send_to_users(db, notification_id, send_request.user_ids)

    return {"message": f"成功发送给 {count} 个用户"}
```

## 4️⃣ 完整的业务流程

### 场景 1：管理员发送站内信给用户

```
┌──────────────────────────────────────────────────────────────┐
│  1. 管理员创建站内信                                           │
│     POST /api/v1/admin/notifications                          │
│     {                                                         │
│       "type": "system",                                       │
│       "title": "系统维护通知",                                 │
│       "content": "今晚22:00系统维护"                           │
│     }                                                         │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  2. NotificationService.create_notification()                │
│     - 创建 Notification 记录                                  │
│     - 返回 notification_id: "msg_001"                         │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  3. 管理员发送站内信                                           │
│     POST /api/v1/admin/notifications/msg_001/send             │
│     {                                                         │
│       "user_ids": ["user_A", "user_B", "user_C"],             │
│       "send_to_all": false                                    │
│     }                                                         │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  4. NotificationService.send_to_users()                       │
│     For each user_id:                                         │
│       - 检查是否已存在 (防止重复)                               │
│       - 创建 NotificationRecord                               │
│         { notification_id: "msg_001", user_id: "user_A" }     │
│         { notification_id: "msg_001", user_id: "user_B" }     │
│         { notification_id: "msg_001", user_id: "user_C" }     │
│     - 批量插入数据库                                          │
│     - 返回成功发送数量: 3                                      │
└──────────────────────────────────────────────────────────────┘
```

### 场景 2：用户查看站内信列表

```
┌──────────────────────────────────────────────────────────────┐
│  1. 用户请求站内信列表                                         │
│     GET /api/v1/notifications?page=1&page_size=20             │
│     Authorization: Bearer <jwt_token>                         │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  2. JWT 认证中间件                                             │
│     - 验证 Token 有效性                                       │
│     - 解析出 user_id: "user_A"                                │
│     - 查询用户信息                                            │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  3. NotificationService.get_user_notifications()             │
│     - 查询用户的 notification_records                         │
│     - 关联 notifications 表获取内容                            │
│     - 过滤已删除 (is_deleted = false)                          │
│     - 按创建时间倒序排序                                       │
│     - 统计未读数量                                            │
│     - 分页返回                                                │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  4. 返回数据                                                   │
│     {                                                         │
│       "total": 100,                                           │
│       "unread_count": 5,                                      │
│       "items": [                                              │
│         {                                                     │
│           "id": "record_001",                                 │
│           "notification": {                                   │
│             "id": "msg_001",                                  │
│             "title": "系统维护通知",                           │
│             "content": "今晚22:00系统维护"                     │
│           },                                                  │
│           "is_read": false,                                   │
│           "created_at": "2025-02-07T10:00:00Z"                │
│         },                                                    │
│         ...                                                   │
│       ]                                                       │
│     }                                                         │
└──────────────────────────────────────────────────────────────┘
```

### 场景 3：用户标记已读

```
┌──────────────────────────────────────────────────────────────┐
│  1. 用户标记站内信为已读                                       │
│     POST /api/v1/notifications/record_001/read                │
│     Authorization: Bearer <jwt_token>                         │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  2. NotificationService.mark_as_read()                        │
│     - 查询站内信记录 (record_001)                              │
│     - 验证是否属于当前用户 (user_id == user_A)                 │
│     - 更新: is_read = true, read_at = now()                   │
│     - 提交事务                                                │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  3. 返回 204 No Content                                       │
└──────────────────────────────────────────────────────────────┘
```

## 5️⃣ 关键技术点总结

### ✅ 1. 内容与记录分离

**实现**：
- `notifications` 表：存储站内信内容（1 份）
- `notification_records` 表：存储用户接收记录（N 份）

**好处**：
- 节省存储空间
- 避免数据冗余
- 便于修改内容

### ✅ 2. 防止重复发送

**数据库层面**：
```sql
UNIQUE(notification_id, user_id)
```

**代码层面**：
```python
existing = db.query(NotificationRecord).filter(
    NotificationRecord.notification_id == notification_id,
    NotificationRecord.user_id == user_id,
).first()

if not existing:
    # 只有不存在时才创建
    records.append(NotificationRecord(...))
```

### ✅ 3. 软删除

**删除时**：
```python
# 只标记不物理删除
record.is_deleted = True
record.deleted_at = datetime.utcnow()
```

**查询时**：
```python
# 过滤已删除的记录
.filter(NotificationRecord.is_deleted == False)
```

**好处**：
- 数据可恢复
- 保留审计日志
- 可用于统计分析

### ✅ 4. 级联删除

**定义**：
```python
notification_id = Column(
    UUID(as_uuid=True),
    ForeignKey("notifications.id", ondelete="CASCADE"),
    nullable=False
)
```

**效果**：
- 删除 `notifications` 记录时
- 自动删除所有关联的 `notification_records`

### ✅ 5. 性能优化

**批量插入**：
```python
# 使用批量插入代替逐条插入
db.bulk_save_objects(records)
db.commit()
```

**索引优化**：
```python
# 在常用查询字段上建立索引
index=True  # user_id, notification_id, is_read, created_at
```

**分页查询**：
```python
# 避免一次性加载大量数据
records = query.offset(skip).limit(limit).all()
```

**关联查询优化**：
```python
# 使用 join 避免 N+1 查询
query = db.query(NotificationRecord)\
    .join(Notification)\
    .filter(...)
```

### ✅ 6. 权限控制

**验证用户权限**：
```python
# 查询时验证用户只能访问自己的站内信
.filter(NotificationRecord.user_id == user_id)
```

**JWT 认证**：
```python
# API 层使用依赖注入进行认证
@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user)  # 自动验证 Token
):
    return NotificationService.get_user_notifications(
        db,
        user_id=str(current_user.id)  # 使用认证后的用户 ID
    )
```

## 🎯 总结

站内信系统的核心实现就是：

### 核心组件
1. **两张表**：`notifications`（内容）+ `notification_records`（记录）
2. **一个服务**：`NotificationService` 处理所有业务逻辑
3. **一组 API**：RESTful 接口供前端调用

### 关键特性
- ✅ 内容与记录分离（避免冗余）
- ✅ 防止重复发送（唯一约束 + 代码检查）
- ✅ 软删除（可恢复、保留审计）
- ✅ 级联删除（数据一致性）
- ✅ 分页筛选（性能优化）
- ✅ 权限控制（JWT 认证）

### 适用场景
- 系统通知（维护、升级、警告）
- 业务通知（订单状态、审批流程）
- 提醒通知（会议、待办事项）
- 公告通知（活动、政策变更）

这个设计既简单又高效，适用于大多数站内信场景！🎉
