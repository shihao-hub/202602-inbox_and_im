# Web 后端开发完整指南：从需求分析到系统设计

## 📋 目录

1. [需求分析篇](#一需求分析篇)
2. [数据库设计篇](#二数据库设计篇)
3. [接口设计篇](#三接口设计篇)
4. [代码实现篇](#四代码实现篇)
5. [实战案例篇](#五实战案例篇)
6. [最佳实践篇](#六最佳实践篇)

---

## 一、需求分析篇

### 1.1 需求分析的三个层次

#### 🎯 第一层：理解业务目标

**核心问题**：这个系统要解决什么问题？

**分析方法**：

- **5W1H 分析法**
  - **Who**：谁会使用这个系统？（目标用户）
  - **What**：系统要提供什么功能？（核心功能）
  - **When**：什么时候使用？（使用场景）
  - **Where**：在哪里使用？（部署环境）
  - **Why**：为什么要开发这个系统？（业务价值）
  - **How**：如何实现？（技术选型）

**示例：站内信系统**

```
Who:  系统用户和管理员
What: 发送和接收站内通知
When: 用户登录后、有重要消息时
Where: Web 平台
Why: 代替邮件，提高消息触达率
How: FastAPI + PostgreSQL + WebSocket
```

#### 📊 第二层：梳理功能需求

**功能需求清单模板**：

| 模块   | 功能    | 优先级 | 复杂度 | 依赖    |
| ---- | ----- | --- | --- | ----- |
| 用户管理 | 注册/登录 | P0  | 中   | 无     |
| 站内信  | 创建站内信 | P0  | 低   | 用户管理  |
| 站内信  | 发送给用户 | P0  | 中   | 创建站内信 |
| 站内信  | 查看列表  | P0  | 中   | 发送给用户 |
| 站内信  | 标记已读  | P1  | 低   | 查看列表  |
| 站内信  | 删除站内信 | P1  | 低   | 查看列表  |

**优先级定义**：

- **P0**：必须有，没有无法上线
- **P1**：重要，影响用户体验
- **P2**：可选，有时间再做

#### 🔍 第三层：挖掘隐性需求

**需要思考的问题**：

1. **数据一致性**
   
   - 用户删除站内信后，管理员还能看到吗？
   - 删除站内信内容，所有用户的记录会删除吗？

2. **并发控制**
   
   - 同一条站内信会被重复发送吗？
   - 多个管理员同时修改同一条站内信会怎样？

3. **性能要求**
   
   - 需要支持多少用户？（100 / 1000 / 10000+）
   - 单次发送最多给多少用户？（100 / 1000 / 10000+）
   - 响应时间要求？（< 100ms / < 500ms / < 1s）

4. **安全要求**
   
   - 用户只能看自己的站内信吗？
   - 管理员权限如何控制？
   - 敏感信息如何加密？

5. **扩展性**
   
   - 未来要支持群发吗？
   - 未来要支持定时发送吗？
   - 未来要支持附件吗？

### 1.2 需求分析检查清单

在开始设计前，确保你能回答以下问题：

- [ ] **业务目标清晰**：能用一句话说明系统要解决的问题
- [ ] **用户角色明确**：知道哪些人会使用系统
- [ ] **功能优先级确定**：区分 P0 / P1 / P2
- [ ] **数据关系理清**：知道核心实体及其关系
- [ ] **非功能需求明确**：性能、安全、可用性要求
- [ ] **技术栈确定**：编程语言、框架、数据库
- [ ] **约束条件明确**：开发时间、团队规模、预算

---

## 二、数据库设计篇

### 2.1 数据库设计的五个步骤

#### Step 1: 识别核心实体

**什么是实体？**

实体就是系统中的"名词"：

- 站内信系统：用户、站内信、站内信记录
- 电商系统：用户、商品、订单、订单项
- 社交系统：用户、帖子、评论、点赞

**方法：** 从需求描述中提取名词

```
需求：用户可以创建站内信，发送给其他用户，
      用户可以查看站内信列表，标记已读

提取实体：
- 用户（User）
- 站内信（Notification）
- 站内信记录（NotificationRecord）
```

#### Step 2: 确定实体关系

**三种基本关系**：

```
1. 一对一（1:1）
   用户 ←→ 用户资料（每个用户一个资料）

2. 一对多（1:N）
   用户 ←→ 站内信记录（一个用户多条记录）

3. 多对多（M:N）
   学生 ←→ 课程（多个学生选多门课）
   → 需要中间表（选课记录）
```

**站内信系统的关系**：

```
User (1) ──< NotificationRecord (M) >── (1) Notification
  ↑                                                    ↑
  │                                                    │
创建者                                              内容
(0..1)                                            (1)
```

#### Step 3: 定义实体属性

**属性设计原则**：

1. **原子性**：每个字段只存储一个值
   
   - ❌ `name: "张三,男,30"`  （多个值）
   - ✅ `name: "张三"` + `gender: "男"` + `age: 30`

2. **不可再分**：避免复合字段
   
   - ❌ `address: "北京市朝阳区xxx街道xxx号"`
   - ✅ `province: "北京市"` + `city: "朝阳区"` + `detail: "xxx街道xxx号"`

3. **必要的冗余**：适度冗余可以提高查询性能
   
   - 考虑：`notifications` 表是否需要存储创建者名称？
   - 决策：不需要，可以通过 `created_by` 关联查询

**站内信系统的属性**：

```python
# User（用户）
- id: UUID（主键）
- username: String（唯一）
- email: String（唯一）
- password_hash: String（加密）
- created_at: DateTime

# Notification（站内信内容）
- id: UUID（主键）
- type: String（枚举）
- title: String
- content: Text
- priority: Integer
- created_by: UUID（外键 → User）
- created_at: DateTime

# NotificationRecord（用户记录）
- id: UUID（主键）
- notification_id: UUID（外键 → Notification）
- user_id: UUID（外键 → User）
- is_read: Boolean
- read_at: DateTime
- created_at: DateTime
```

#### Step 4: 规范化与反规范化

**范式等级**：

| 范式  | 说明      | 示例           |
| --- | ------- | ------------ |
| 1NF | 每个字段原子性 | 将复合地址拆分为省市区  |
| 2NF | 消除部分依赖  | 非主键字段完全依赖于主键 |
| 3NF | 消除传递依赖  | A→B→C 改为 A→C |

**站内信系统的 3NF 检查**：

```
❌ 不符合 3NF 的设计：
NotificationRecord {
  notification_id,
  user_id,
  notification_title,  # 冗余！可以通过 notification_id 获取
  notification_content, # 冗余！
  is_read
}

✅ 符合 3NF 的设计：
NotificationRecord {
  notification_id,  # 只存 ID
  user_id,
  is_read
}
# 需要时通过 JOIN 查询 notification 表获取标题和内容
```

**什么时候反规范化？**

1. **查询性能要求高**
   
   - 每次查询都需要 JOIN，影响性能
   - 可以适度冗余常用字段

2. **历史数据不变**
   
   - 订单快照：保存下单时的商品价格
   - 日志记录：保存操作时的完整状态

**站内信系统的反规范化决策**：

```
❌ 不推荐冗余：
- notification.title（标题可能修改）
- notification.content（内容可能修改）

✅ 可以考虑冗余：
- sender.username（发送者名称不变）
- notification.type（类型一般不变）
```

#### Step 5: 索引优化

**索引设计原则**：

1. **经常查询的字段**
   
   ```python
   # WHERE 条件
   .filter(User.id == user_id)  # → 索引 user_id
   .filter(Notification.type == "system")  # → 索引 type
   ```

2. **经常排序的字段**
   
   ```python
   # ORDER BY
   .order_by(NotificationRecord.created_at.desc())  # → 索引 created_at
   ```

3. **外键字段**
   
   ```python
   # JOIN 条件
   .join(Notification)  # → 索引 notification_id
   ```

4. **唯一约束**
   
   ```python
   # 防止重复
   UniqueConstraint("notification_id", "user_id")
   ```

**站内信系统的索引设计**：

```sql
-- users 表
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- notifications 表
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_created_by ON notifications(created_by);

-- notification_records 表
CREATE INDEX idx_records_user_id ON notification_records(user_id);
CREATE INDEX idx_records_notification_id ON notification_records(notification_id);
CREATE INDEX idx_records_created_at ON notification_records(created_at DESC);

-- 复合索引（查询优化）
CREATE INDEX idx_records_user_unread ON notification_records(user_id, is_read, created_at DESC)
  WHERE is_deleted = FALSE;
```

### 2.2 数据库设计检查清单

- [ ] **实体识别完整**：没有遗漏重要实体
- [ ] **关系定义清晰**：知道 1:1 / 1:N / M:N 关系
- [ ] **属性设计合理**：满足原子性，避免冗余
- [ ] **范式级别合适**：一般 3NF，适度反规范化
- [ ] **索引设计完善**：覆盖常用查询场景
- [ ] **约束条件明确**：主键、外键、唯一约束、非空约束
- [ ] **数据类型合适**：使用合适的数据类型和长度
- [ ] **扩展性考虑**：预留字段或表结构易于扩展

---

## 三、接口设计篇

### 3.1 RESTful API 设计原则

#### 📐 RESTful 风格规范

**资源命名**：

```
✅ 好的命名：
- /api/v1/notifications（站内信资源）
- /api/v1/users（用户资源）
- /api/v1/friends（好友资源）

❌ 不好的命名：
- /api/v1/getNotifications（动词）
- /api/v1/notification_list（不必要的后缀）
- /api/v1/notification-data（不清晰）
```

**HTTP 方法映射**：

| 方法     | 操作   | 示例                                  | 是否幂等 |
| ------ | ---- | ----------------------------------- | ---- |
| GET    | 查询   | `GET /api/v1/notifications`         | ✅ 是  |
| POST   | 创建   | `POST /api/v1/notifications`        | ❌ 否  |
| PUT    | 完整更新 | `PUT /api/v1/notifications/{id}`    | ✅ 是  |
| PATCH  | 部分更新 | `PATCH /api/v1/notifications/{id}`  | ❌ 否  |
| DELETE | 删除   | `DELETE /api/v1/notifications/{id}` | ✅ 是  |

**状态码使用**：

```
2xx 成功：
- 200 OK - 查询成功
- 201 Created - 创建成功
- 204 No Content - 删除成功（无返回内容）

4xx 客户端错误：
- 400 Bad Request - 参数错误
- 401 Unauthorized - 未认证
- 403 Forbidden - 无权限
- 404 Not Found - 资源不存在
- 422 Unprocessable Entity - 数据验证失败

5xx 服务器错误：
- 500 Internal Server Error - 服务器内部错误
```

#### 🎯 接口设计实例

**设计原则**：
1. **路径参数在末尾**：路径参数只能有一个，且必须在 URL 的最末尾
2. **路由语义化**：让人一眼就能看懂是干什么的
3. **部分 RESTful**：保持 RESTful 的好处，但不死板

**站内信用户端 API**：

```
# 1. 获取站内信列表
GET /api/v1/notifications?page=1&page_size=20&is_read=false
Response: {
  "total": 100,
  "unread_count": 5,
  "items": [...]
}

# 2. 获取未读数量（独立端点，语义清晰）
GET /api/v1/notifications/unread-count
Response: {"unread_count": 5}

# 3. 获取站内信详情（路径参数在末尾）
GET /api/v1/notifications/{record_id}
Response: {
  "id": "record_001",
  "notification": {...},
  "is_read": false,
  "created_at": "2025-02-07T10:00:00Z"
}

# 4. 标记单条已读（使用查询参数，路径参数在末尾）
POST /api/v1/notifications/{record_id}?action=mark-read
Body: {}
Response: 204 No Content

# 5. 标记全部已读（独立动作，无路径参数）
POST /api/v1/notifications/mark-all-read
Body: {}
Response: {"message": "已将 10 条站内信标记为已读"}

# 6. 删除站内信（标准 RESTful，路径参数在末尾）
DELETE /api/v1/notifications/{record_id}
Response: 204 No Content
```

**设计说明**：
- ✅ **路径参数在末尾**：`{record_id}` 始终在 URL 末尾，后面没有其他路径段
- ✅ **语义化**：`action=mark-read` 明确表示操作类型
- ✅ **避免嵌套**：没有 `/{id}/mark-read` 这种路径参数在中间的设计

**站内信管理端 API**：

```
# 1. 创建站内信（标准 RESTful）
POST /api/v1/admin/notifications
Body: {
  "type": "system",
  "title": "系统维护通知",
  "content": "今晚22:00系统维护",
  "priority": 0
}
Response: {
  "id": "msg_001",
  "type": "system",
  "title": "系统维护通知",
  ...
}

# 2. 获取站内信管理列表
GET /api/v1/admin/notifications?page=1&page_size=20
Response: {
  "total": 50,
  "items": [...]
}

# 3. 获取站内信详情（路径参数在末尾）
GET /api/v1/admin/notifications/{notification_id}
Response: {...}

# 4. 更新站内信（标准 RESTful，路径参数在末尾）
PUT /api/v1/admin/notifications/{notification_id}
Body: {
  "title": "系统维护通知（已更新）",
  "priority": 1
}
Response: {...}

# 5. 删除站内信（标准 RESTful，路径参数在末尾）
DELETE /api/v1/admin/notifications/{notification_id}
Response: 204 No Content

# 6. 发送站内信（使用查询参数，路径参数在末尾）
POST /api/v1/admin/notifications/{notification_id}?action=send-to-users
Body: {
  "user_ids": ["user_A", "user_B"],
  "send_to_all": false
}
Response: {"message": "成功发送给 2 个用户"}
```

**设计说明**：
- ✅ **路径参数在末尾**：`{notification_id}` 在最末尾，使用查询参数 `action` 指定具体操作
- ✅ **动作语义化**：`action=send-to-users` 比 `send` 更明确
- ✅ **灵活扩展**：同一个资源可以通过不同的 `action` 执行不同操作

**对比：错误设计 vs 正确设计**

```
❌ 错误设计（路径参数在中间）：
PUT /api/v1/notifications/{record_id}/mark-read
POST /api/v1/admin/notifications/{notification_id}/send-to-users
GET /api/v1/users/{user_id}/notifications/{notification_id}

✅ 正确设计（路径参数在末尾）：
POST /api/v1/notifications/{record_id}?action=mark-read
POST /api/v1/admin/notifications/{notification_id}?action=send-to-users
GET /api/v1/notification-records/{id}  # 扁平化设计
```

**更多示例**：

```
# ❌ 错误设计（路径参数在中间）
POST /api/v1/users/{id}/verify-email
POST /api/v1/users/{id}/reset-password
POST /api/v1/orders/{id}/cancel
POST /api/v1/payments/{id}/refund

# ✅ 正确设计（路径参数在末尾 + 查询参数）
POST /api/v1/users/{id}?action=verify-email
POST /api/v1/users/{id}?action=reset-password
POST /api/v1/orders/{id}?action=cancel
POST /api/v1/payments/{id}?action=refund

# ✅ 或者完全无路径参数，通过 body 传递
POST /api/v1/users/verify-email
Body: {"user_id": "xxx"}

POST /api/v1/users/reset-password
Body: {"user_id": "xxx"}

POST /api/v1/orders/cancel
Body: {"order_id": "xxx"}
```

**设计模式总结**：

| 模式 | 适用场景 | 示例 |
|------|---------|------|
| **标准 RESTful** | CRUD 操作 | `GET /{id}`、`DELETE /{id}` |
| **查询参数模式** | 对资源执行特定操作 | `POST /{id}?action=xxx` |
| **独立端点模式** | 批量操作或跨资源操作 | `POST /mark-all-read` |
| **Body 参数模式** | 复杂业务操作 | `POST /verify-email` + body |

### 3.2 接口设计最佳实践

#### ✅ DO（推荐做法）

1. **路径参数在末尾**

   ```
   ✅ GET /api/v1/notifications/{id}
   ✅ POST /api/v1/notifications/{id}?action=mark-read
   ✅ DELETE /api/v1/notifications/{id}
   ❌ POST /api/v1/notifications/{id}/mark-read
   ❌ GET /api/v1/users/{user_id}/notifications/{notification_id}
   ```

2. **使用查询参数指定操作**

   ```
   ✅ POST /api/v1/notifications/{id}?action=mark-read
   ✅ POST /api/v1/admin/notifications/{id}?action=send-to-users
   ❌ POST /api/v1/notifications/{id}/mark-read
   ```

3. **路由语义化，一眼就懂**

   ```
   ✅ ?action=mark-read
   ✅ ?action=send-to-users
   ✅ ?action=reset-password
   ❌ ?action=read（不够明确）
   ❌ ?action=send（发送什么？）
   ```

4. **使用版本号**

   ```
   /api/v1/notifications
   /api/v2/notifications  # 新版本
   ```

5. **使用复数名词**

   ```
   ✅ /api/v1/users
   ❌ /api/v1/user
   ```

6. **使用查询参数过滤**

   ```
   GET /api/v1/notifications?type=system&is_read=false&page=1
   ```

7. **统一响应格式**

   ```json
   {
     "code": 200,
     "message": "success",
     "data": {...}
   }
   ```

8. **提供分页信息**

   ```json
   {
     "total": 100,
     "page": 1,
     "page_size": 20,
     "items": [...]
   }
   ```

#### ❌ DON'T（不推荐做法）

1. **路径参数在中间**

   ```
   ❌ POST /api/v1/notifications/{id}/mark-read
   ❌ POST /api/v1/notifications/{id}/send
   ❌ GET /api/v1/users/{id}/notifications/{id}/read
   ✅ POST /api/v1/notifications/{id}?action=mark-read
   ✅ GET /api/v1/notification-records/{id}
   ```

2. **多个路径参数或嵌套过深**

   ```
   ❌ /api/v1/users/{id}/notifications/{id}/records/{id}
   ❌ /api/v1/users/{id}/posts/{id}/comments/{id}
   ✅ /api/v1/notification-records/{id}
   ```

3. **不够语义化的操作**

   ```
   ❌ ?action=read
   ❌ ?action=send
   ✅ ?action=mark-read
   ✅ ?action=send-to-users
   ```

4. **在 URL 路径中使用动词**

   ```
   ❌ /api/v1/getNotifications
   ❌ /api/v1/createNotification
   ✅ /api/v1/notifications (GET/POST 区分)
   ```

5. **返回过多数据**

   ```
   ❌ 一次性返回 10000 条记录
   ✅ 使用分页，每页 20-50 条
   ```

6. **不使用状态码**

   ```
   ❌ 所有请求都返回 200，错误信息在 body 里
   ✅ 使用正确的 HTTP 状态码
   ```

### 3.3 设计原则总结

#### 三大原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **1. 路径参数在末尾** | 路径参数只能有一个，且必须在 URL 最末尾 | `/{id}?action=xxx` ✅<br>`/{id}/action` ❌ |
| **2. 路由语义化** | 让人一眼看懂是干什么的 | `action=mark-read` ✅<br>`action=read` ❌ |
| **3. 部分RESTful** | 保持 RESTful 好处，但不死板 | `POST /{id}?action=xxx` ✅ |

#### 四种推荐模式

| 模式 | URL 格式 | 适用场景 | 示例 |
|------|---------|---------|------|
| **标准 RESTful** | `METHOD /resource/{id}` | CRUD 操作 | `GET /{id}`、`DELETE /{id}` |
| **查询参数模式** | `POST /resource/{id}?action=xxx` | 对资源执行特定操作 | `POST /{id}?action=mark-read` |
| **独立端点模式** | `POST /resource/action` | 批量操作或跨资源操作 | `POST /mark-all-read` |
| **Body 参数模式** | `POST /resource/action` + body | 复杂业务操作 | `POST /verify-email` |

#### RESTful 适用场景

**完全符合 RESTful**：
- ✅ CRUD 操作（GET/POST/PUT/DELETE）
- ✅ 资源集合查询
- ✅ 单资源操作

**适度偏离 RESTful**：
- ✅ 动作操作（使用 `?action=xxx`）
- ✅ 批量操作（独立端点）
- ✅ 业务特定动作（approve、reject、cancel）

#### 命名规范

| 操作类型 | action 参数值 | 示例 |
|---------|--------------|------|
| 标记操作 | `mark-{status}` | `action=mark-read`、`action=mark-important` |
| 批量标记 | `mark-all-{status}` | `action=mark-all-read` |
| 发送操作 | `send-to-{target}` | `action=send-to-users`、`action=send-to-group` |
| 验证操作 | `verify-{object}` | `action=verify-email`、`action=verify-phone` |
| 重置操作 | `reset-{object}` | `action=reset-password` |
| 请求操作 | `request-{action}` | `action=request-cancellation`、`action=request-approval` |
| 审批操作 | `approve` / `reject` | `action=approve`、`action=reject` |

### 3.4 接口设计检查清单

- [ ] **路径参数在末尾**：路径参数只能有一个，且必须在 URL 最末尾
- [ ] **使用查询参数指定操作**：避免路径嵌套，使用 `?action=xxx`
- [ ] **路由语义化**：action 值要清晰明确
- [ ] **RESTful 风格**：基本遵循 RESTful，但不死板
- [ ] **HTTP 方法正确**：GET/POST/PUT/DELETE 使用得当
- [ ] **状态码合理**：使用正确的 HTTP 状态码
- [ ] **版本控制**：URL 中包含版本号
- [ ] **统一响应格式**：成功和错误都有统一的格式
- [ ] **分页支持**：列表接口支持分页
- [ ] **过滤和排序**：支持查询参数进行过滤和排序
- [ ] **幂等性考虑**：PUT/DELETE 等操作保证幂等
- [ ] **错误处理**：返回清晰的错误信息
- [ ] **文档完善**：每个接口都有文档说明

---

## 四、代码实现篇

### 4.1 分层架构设计

**标准分层架构**：

```
┌─────────────────────────────────────┐
│         API 层（路由）               │  ← 处理 HTTP 请求
│  app/api/v1/notifications.py        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│       业务逻辑层（Service）          │  ← 核心业务逻辑
│  app/services/notification_service.py│
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      数据访问层（Model）             │  ← 数据库操作
│  app/models/notification.py         │
└─────────────────────────────────────┘
```

**各层职责**：

#### API 层（路由层）

**职责**：

- 接收 HTTP 请求
- 参数验证
- 调用业务逻辑层
- 返回 HTTP 响应

**示例**：

```python
@router.get("", response_model=NotificationRecordListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),  # 权限验证
    db: Session = Depends(get_db),                    # 依赖注入
):
    """获取站内信列表"""
    skip = (page - 1) * page_size

    # 调用业务逻辑层
    return NotificationService.get_user_notifications(
        db,
        user_id=str(current_user.id),
        skip=skip,
        limit=page_size,
    )
```

**关键点**：

- 不要在这里写业务逻辑
- 只做参数验证和调用 Service
- 使用依赖注入处理横切关注点（认证、数据库）

#### 业务逻辑层（Service 层）

**职责**：

- 实现核心业务逻辑
- 协调多个 Model
- 处理业务规则
- 事务控制

**示例**：

```python
class NotificationService:
    @staticmethod
    def send_to_users(db: Session, notification_id: str, user_ids: List[str]) -> int:
        """发送站内信给指定用户"""

        # 1. 验证站内信是否存在
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        if not notification:
            raise HTTPException(status_code=404, detail="站内信不存在")

        # 2. 批量创建用户记录
        records = []
        for user_id in user_ids:
            # 检查是否已存在（业务规则：防止重复发送）
            existing = db.query(NotificationRecord).filter(
                NotificationRecord.notification_id == notification_id,
                NotificationRecord.user_id == user_id,
            ).first()

            if not existing:
                records.append(NotificationRecord(
                    notification_id=notification_id,
                    user_id=user_id,
                ))

        # 3. 批量保存（性能优化）
        db.bulk_save_objects(records)
        db.commit()  # 事务提交

        return len(records)
```

**关键点**：

- 一个方法做一件事
- 处理所有业务逻辑
- 使用事务保证数据一致性
- 抛出清晰的异常

#### 数据访问层（Model 层）

**职责**：

- 定义数据结构
- ORM 映射
- 数据验证

**示例**：

```python
class Notification(Base):
    """站内信内容表"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 关系
    records = relationship("NotificationRecord", back_populates="notification", cascade="all, delete-orphan")
```

**关键点**：

- 只定义数据结构
- 不包含业务逻辑
- 使用 ORM 关系映射

### 4.2 依赖注入的使用

**什么是依赖注入？**

依赖注入（Dependency Injection）是一种设计模式，用于实现控制反转（IoC）。

**FastAPI 的依赖注入**：

```python
# 1. 定义依赖
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    user = verify_token(token, db)
    return user

# 2. 使用依赖
@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),  # 自动注入
    db: Session = Depends(get_db),                    # 自动注入
):
    # 直接使用注入的对象
    return NotificationService.get_user_notifications(
        db,
        user_id=str(current_user.id)
    )
```

**好处**：

- 代码复用
- 测试友好（可以 mock 依赖）
- 关注点分离

### 4.3 异常处理

**统一异常处理**：

```python
# 1. 自定义异常
class NotificationNotFoundException(Exception):
    """站内信不存在异常"""
    pass

class DuplicateNotificationException(Exception):
    """重复发送异常"""
    pass

# 2. 全局异常处理器
@app.exception_handler(NotificationNotFoundException)
async def notification_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "站内信不存在"}
    )

# 3. 在 Service 中使用
class NotificationService:
    def get_notification(self, db: Session, notification_id: str):
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            raise NotificationNotFoundException()

        return notification
```

### 4.4 代码实现检查清单

- [ ] **分层清晰**：API / Service / Model 职责明确
- [ ] **依赖注入**：使用依赖注入管理横切关注点
- [ ] **异常处理**：有统一的异常处理机制
- [ ] **日志记录**：关键操作有日志记录
- [ ] **数据验证**：使用 Pydantic 进行数据验证
- [ ] **事务管理**：数据库操作使用事务
- [ ] **代码复用**：避免重复代码
- [ ] **测试覆盖**：有单元测试和集成测试

---

## 五、实战案例篇

### 5.1 完整开发流程演示

让我们以"站内信系统"为例，演示完整的开发流程。

#### 阶段 1：需求分析（1-2 小时）

**Step 1: 理解业务**

```
业务目标：提供一个站内消息通知系统，用于：
- 系统通知（维护、升级）
- 业务通知（订单状态、审批流程）
- 用户间消息（可选）

目标用户：
- 普通用户：接收和查看站内信
- 管理员：创建和发送站内信
```

**Step 2: 功能清单**

| 功能模块 | 功能点   | 优先级 | 依赖    |
| ---- | ----- | --- | ----- |
| 用户认证 | 注册/登录 | P0  | 无     |
| 站内信  | 创建站内信 | P0  | 用户认证  |
| 站内信  | 发送给用户 | P0  | 创建站内信 |
| 站内信  | 查看列表  | P0  | 发送给用户 |
| 站内信  | 标记已读  | P1  | 查看列表  |
| 站内信  | 删除站内信 | P1  | 查看列表  |

**Step 3: 非功能需求**

```
性能：
- 支持 1000+ 用户
- 单次发送支持 100+ 用户
- 列表查询 < 500ms

安全：
- JWT 认证
- 用户只能看自己的站内信
- 管理员权限控制

扩展性：
- 预留群发接口
- 预留定时发送
- 预留附件功能
```

#### 阶段 2：数据库设计（2-3 小时）

**Step 1: 识别实体**

```
核心实体：
1. User（用户）
2. Notification（站内信内容）
3. NotificationRecord（站内信记录）
```

**Step 2: 设计关系**

```
User (1) ──< NotificationRecord (M) >── (1) Notification
  ↑                                                    ↑
创建者                                              内容
```

**Step 3: 设计表结构**

```sql
-- users 表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- notifications 表
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- notification_records 表
CREATE TABLE notification_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(notification_id, user_id)
);
```

**Step 4: 索引设计**

```sql
CREATE INDEX idx_records_user_id ON notification_records(user_id);
CREATE INDEX idx_records_is_read ON notification_records(is_read);
CREATE INDEX idx_records_created_at ON notification_records(created_at DESC);
```

#### 阶段 3：接口设计（1-2 小时）

**用户端 API**：

```
GET    /api/v1/notifications           # 获取列表
GET    /api/v1/notifications/{id}      # 获取详情
POST   /api/v1/notifications/{id}/read # 标记已读
DELETE /api/v1/notifications/{id}      # 删除
```

**管理端 API**：

```
POST   /api/v1/admin/notifications           # 创建
GET    /api/v1/admin/notifications           # 列表
PUT    /api/v1/admin/notifications/{id}      # 更新
DELETE /api/v1/admin/notifications/{id}      # 删除
POST   /api/v1/admin/notifications/{id}/send # 发送
```

#### 阶段 4：代码实现（3-5 天）

**Day 1: 搭建框架**

- 创建项目结构
- 配置数据库连接
- 实现用户认证

**Day 2: 数据模型**

- 创建 Model
- 编写迁移脚本
- 初始化数据库

**Day 3: 业务逻辑**

- 实现 NotificationService
- 实现核心业务方法

**Day 4: API 开发**

- 实现用户端 API
- 实现管理端 API

**Day 5: 测试和优化**

- 编写单元测试
- 性能优化
- Bug 修复

### 5.2 常见问题与解决方案

#### 问题 1: 如何防止重复发送？

**场景**：管理员可能多次点击"发送"按钮

**解决方案**：

```python
# 方案一：数据库唯一约束
class NotificationRecord(Base):
    __table_args__ = (
        UniqueConstraint('notification_id', 'user_id', name='unique_notification_user'),
    )

# 方案二：代码层面检查
def send_to_users(db, notification_id, user_ids):
    for user_id in user_ids:
        existing = db.query(NotificationRecord).filter(
            NotificationRecord.notification_id == notification_id,
            NotificationRecord.user_id == user_id,
        ).first()

        if not existing:
            # 只有不存在才创建
            record = NotificationRecord(...)
            db.add(record)
```

#### 问题 2: 如何处理大批量发送？

**场景**：需要发送给 10000+ 用户

**解决方案**：

```python
# 方案一：批量插入
def send_to_users(db, notification_id, user_ids):
    records = [
        NotificationRecord(notification_id=notification_id, user_id=user_id)
        for user_id in user_ids
    ]
    db.bulk_save_objects(records)  # 批量插入，性能更好
    db.commit()

# 方案二：使用消息队列（异步）
@celery.task
def send_notification_async(notification_id, user_ids):
    # 后台异步处理
    pass

# 调用
send_notification_async.delay(notification_id, user_ids)
```

#### 问题 3: 如何优化列表查询性能？

**场景**：用户有 10000+ 条站内信记录

**解决方案**：

```python
# 方案一：分页
def get_notifications(db, user_id, page=1, page_size=20):
    return db.query(NotificationRecord)\
        .filter(NotificationRecord.user_id == user_id)\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()

# 方案二：复合索引
CREATE INDEX idx_user_unread_time
ON notification_records(user_id, is_read, created_at DESC)
WHERE is_deleted = FALSE;

# 方案三：缓存未读数
@cache.memoize(timeout=60)  # 缓存 60 秒
def get_unread_count(db, user_id):
    return db.query(NotificationRecord).filter(
        NotificationRecord.user_id == user_id,
        NotificationRecord.is_read == False
    ).count()
```

---

## 六、最佳实践篇

### 6.1 需求分析最佳实践

#### ✅ DO

1. **画图理解需求**
   
   - 用流程图描述业务流程
   - 用 ER 图描述数据关系
   - 用时序图描述交互流程

2. **问清楚需求**
   
   - 这个功能为什么需要？
   - 谁会使用？什么时候用？
   - 预期有多少用户？
   - 性能要求是什么？

3. **分阶段实现**
   
   - 先实现核心功能（P0）
   - 再实现重要功能（P1）
   - 最后实现可选功能（P2）

#### ❌ DON'T

1. **不要急于编码**
   
   - 需求不清楚就开始写代码
   - 边写边改，浪费更多时间

2. **不要忽视非功能需求**
   
   - 只关注功能，不考虑性能
   - 只考虑实现，不考虑安全

3. **不要一次性设计太多**
   
   - 试图一次性实现所有功能
   - 过度设计，增加复杂度

### 6.2 数据库设计最佳实践

#### ✅ DO

1. **从需求到表**
   
   - 先理解业务，再设计表结构
   - 实体 → 属性 → 关系

2. **规范命名**
   
   - 表名：小写+下划线（`notification_records`）
   - 字段名：描述性（`created_at` 而非 `time`）
   - 索引名：`idx_表名_字段名`

3. **适当索引**
   
   - 为常用查询字段建索引
   - 为外键建索引
   - 为排序字段建索引

#### ❌ DON'T

1. **不要过度规范化**
   
   - 为了满足范式而牺牲性能
   - 适度冗余是可以接受的

2. **不要忽视数据类型**
   
   - 全部用 `TEXT`
   - 应该用 `INTEGER` 的用了 `VARCHAR`

3. **不要忘记外键**
   
   - 不使用外键约束
   - 依赖应用层维护数据一致性

### 6.3 接口设计最佳实践

#### ✅ DO

1. **RESTful 风格**
   
   - 使用资源命名
   - 正确使用 HTTP 方法

2. **统一响应格式**
   
   ```json
   {
     "code": 200,
     "message": "success",
     "data": {...}
   }
   ```

3. **完善的错误信息**
   
   ```json
   {
     "code": 400,
     "message": "参数验证失败",
     "errors": {
       "email": "邮箱格式不正确"
     }
   }
   ```

#### ❌ DON'T

1. **不要在 URL 中使用动词**
   
   - ❌ `/api/v1/getNotifications`
   - ✅ `/api/v1/notifications`

2. **不要返回过多数据**
   
   - 一次性返回所有数据
   - 应该使用分页

3. **不要忽视版本控制**
   
   - API 升级时不兼容
   - 应该使用 `/api/v1/` `/api/v2/`

### 6.4 代码实现最佳实践

#### ✅ DO

1. **分层架构**
   
   - API / Service / Model 职责明确
   - 每层只做自己的事情

2. **依赖注入**
   
   - 使用 FastAPI 的依赖注入
   - 便于测试和维护

3. **统一异常处理**
   
   - 自定义异常类型
   - 全局异常处理器

4. **编写测试**
   
   - 单元测试覆盖核心逻辑
   - 集成测试覆盖 API

#### ❌ DON'T

1. **不要在 API 层写业务逻辑**
   
   - 所有逻辑都写在路由函数中
   - 应该抽离到 Service 层

2. **不要忽视代码复用**
   
   - 复制粘贴代码
   - 应该抽离公共方法

3. **不要硬编码**
   
   - 配置信息写在代码中
   - 应该使用配置文件

---

## 📚 总结

### 完整开发流程回顾

```
1. 需求分析（理解要做什么）
   ├─ 业务目标（5W1H）
   ├─ 功能清单（P0/P1/P2）
   └─ 非功能需求（性能、安全）

2. 数据库设计（设计数据结构）
   ├─ 识别实体
   ├─ 确定关系
   ├─ 定义属性
   ├─ 规范化
   └─ 索引优化

3. 接口设计（设计 API）
   ├─ RESTful 风格
   ├─ HTTP 方法
   ├─ 响应格式
   └─ 错误处理

4. 代码实现（编写代码）
   ├─ 分层架构
   ├─ 依赖注入
   ├─ 异常处理
   └─ 测试

5. 测试和优化
   ├─ 单元测试
   ├─ 集成测试
   └─ 性能优化
```

### 关键要点

1. **先理解，再设计，最后编码**
   
   - 不要急于编码
   - 花时间理解需求
   - 做好设计很重要

2. **简单设计，逐步迭代**
   
   - 不要过度设计
   - 先实现核心功能
   - 逐步优化和扩展

3. **重视质量**
   
   - 编写测试
   - 代码审查
   - 文档完善

### 推荐阅读

- [站内信系统实现原理详解](./notification-implementation.md) - 本项目的实现细节
- [数据库设计文档](../database-schema.md) - 完整的数据库设计
- [API 文档](../api-documentation.md) - 接口使用说明

---

**最后建议**：

- 多实践，多总结
- 参考优秀开源项目
- 保持代码简洁和可维护

**祝开发顺利！** 🎉
