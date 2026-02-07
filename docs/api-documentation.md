# API 文档

## 概述

本文档详细描述了站内信与即时通讯系统的所有 API 端点。

**Base URL**: `http://localhost:8000`

**API Version**: v1

**Prefix**: `/api/v1`

## 认证机制

本系统使用 JWT（JSON Web Token）进行身份验证。

### Token 类型

1. **Access Token**: 用于访问受保护的 API，有效期 15 分钟
2. **Refresh Token**: 用于刷新 Access Token，有效期 7 天

### 使用方式

在请求头中添加 Authorization 字段：

```
Authorization: Bearer <access_token>
```

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 成功（无返回内容） |
| 400 | 请求参数错误 |
| 401 | 未授权（token 无效或过期） |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

---

## 认证 API

### 1. 用户注册

**Endpoint**: `POST /api/v1/auth/register`

**描述**: 创建新用户账号

**请求体**:

```json
{
  "username": "string (3-50 字符)",
  "email": "string (邮箱格式)",
  "password": "string (至少 6 字符)"
}
```

**响应** (201):

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "avatar_url": "string | null",
  "status": "offline",
  "last_login_at": "ISO8601 datetime | null",
  "created_at": "ISO8601 datetime",
  "updated_at": "ISO8601 datetime"
}
```

**错误响应** (400):

```json
{
  "detail": "用户名已存在"
}
```

---

### 2. 用户登录

**Endpoint**: `POST /api/v1/auth/login`

**描述**: 用户登录并获取 Token

**请求体**:

```json
{
  "username": "string (用户名或邮箱)",
  "password": "string"
}
```

**响应** (200):

```json
{
  "access_token": "string (JWT)",
  "refresh_token": "string (JWT)",
  "token_type": "bearer"
}
```

**错误响应** (401):

```json
{
  "detail": "用户名或密码错误"
}
```

---

### 3. 刷新 Token

**Endpoint**: `POST /api/v1/auth/refresh`

**描述**: 使用 Refresh Token 获取新的 Access Token

**请求体**:

```json
{
  "token": "string (Refresh Token)"
}
```

**响应** (200):

```json
{
  "access_token": "string (新的 JWT)",
  "refresh_token": "string (新的 JWT)",
  "token_type": "bearer"
}
```

**错误响应** (401):

```json
{
  "detail": "无效的 Refresh Token"
}
```

---

### 4. 获取当前用户信息

**Endpoint**: `GET /api/v1/auth/me`

**描述**: 获取当前登录用户的信息

**请求头**:

```
Authorization: Bearer <access_token>
```

**响应** (200):

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "avatar_url": "string | null",
  "status": "offline",
  "last_login_at": "ISO8601 datetime | null",
  "created_at": "ISO8601 datetime",
  "updated_at": "ISO8601 datetime"
}
```

---

### 5. 用户登出

**Endpoint**: `POST /api/v1/auth/logout`

**描述**: 用户登出（客户端需删除本地 Token）

**请求头**:

```
Authorization: Bearer <access_token>
```

**响应** (200):

```json
{
  "message": "登出成功，请删除客户端 Token"
}
```

---

## 站内信 API（用户端）

### 1. 获取站内信列表

**Endpoint**: `GET /api/v1/notifications`

**描述**: 获取当前用户的站内信列表，支持分页和筛选

**请求头**:

```
Authorization: Bearer <access_token>
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_read | boolean | 否 | 筛选已读/未读 |
| notification_type | string | 否 | 站内信类型（system/business/reminder/announcement） |
| page | integer | 否 | 页码（默认 1） |
| page_size | integer | 否 | 每页数量（默认 20，最大 100） |

**示例请求**:

```
GET /api/v1/notifications?is_read=false&page=1&page_size=20
```

**响应** (200):

```json
{
  "total": 100,
  "unread_count": 5,
  "items": [
    {
      "id": "uuid",
      "notification": {
        "id": "uuid",
        "type": "system",
        "title": "系统通知",
        "content": "通知内容",
        "action_url": "https://example.com | null",
        "priority": 0,
        "created_by": "uuid | null",
        "created_at": "ISO8601 datetime",
        "expires_at": "ISO8601 datetime | null"
      },
      "is_read": false,
      "read_at": "ISO8601 datetime | null",
      "created_at": "ISO8601 datetime"
    }
  ]
}
```

---

### 2. 获取未读数量

**Endpoint**: `GET /api/v1/notifications/unread-count`

**描述**: 获取当前用户的未读站内信数量

**请求头**:

```
Authorization: Bearer <access_token>
```

**响应** (200):

```json
{
  "unread_count": 5
}
```

---

### 3. 获取站内信详情

**Endpoint**: `GET /api/v1/notifications/{record_id}`

**描述**: 获取指定站内信的详细信息

**请求头**:

```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| record_id | string | 站内信记录 ID |

**响应** (200):

```json
{
  "id": "uuid",
  "notification": {
    "id": "uuid",
    "type": "system",
    "title": "系统通知",
    "content": "通知内容",
    "action_url": "https://example.com | null",
    "priority": 0,
    "created_by": "uuid | null",
    "created_at": "ISO8601 datetime",
    "expires_at": "ISO8601 datetime | null"
  },
  "is_read": false,
  "read_at": "ISO8601 datetime | null",
  "created_at": "ISO8601 datetime"
}
```

---

### 4. 标记已读

**Endpoint**: `POST /api/v1/notifications/{record_id}/read`

**描述**: 将指定站内信标记为已读

**请求头**:

```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| record_id | string | 站内信记录 ID |

**响应** (204): 无内容

---

### 5. 全部标记已读

**Endpoint**: `POST /api/v1/notifications/read-all`

**描述**: 将当前用户的所有未读站内信标记为已读

**请求头**:

```
Authorization: Bearer <access_token>
```

**响应** (200):

```json
{
  "message": "已将 10 条站内信标记为已读"
}
```

---

### 6. 删除站内信

**Endpoint**: `DELETE /api/v1/notifications/{record_id}`

**描述**: 删除指定站内信（软删除）

**请求头**:

```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| record_id | string | 站内信记录 ID |

**响应** (204): 无内容

---

## 站内信管理 API（管理端）

### 1. 创建站内信

**Endpoint**: `POST /api/v1/admin/notifications`

**描述**: 创建新的站内信（仅创建内容，不发送给用户）

**请求头**:

```
Authorization: Bearer <access_token>
```

**请求体**:

```json
{
  "type": "system",
  "title": "string (1-200 字符)",
  "content": "string",
  "action_url": "string (0-500 字符) | null",
  "priority": 0,
  "expires_at": "ISO8601 datetime | null"
}
```

**字段说明**:

- **type**: 站内信类型
  - `system`: 系统通知
  - `business`: 业务通知
  - `reminder`: 提醒通知
  - `announcement`: 公告
- **priority**: 优先级
  - `0`: 普通
  - `1`: 重要
  - `2`: 紧急

**响应** (201):

```json
{
  "id": "uuid",
  "type": "system",
  "title": "系统通知",
  "content": "通知内容",
  "action_url": "https://example.com | null",
  "priority": 0,
  "created_by": "uuid",
  "created_at": "ISO8601 datetime",
  "expires_at": "ISO8601 datetime | null"
}
```

---

### 2. 获取站内信管理列表

**Endpoint**: `GET /api/v1/admin/notifications`

**描述**: 获取所有创建的站内信内容（不含用户记录）

**请求头**:

```
Authorization: Bearer <access_token>
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | integer | 否 | 跳过数量（默认 0） |
| limit | integer | 否 | 返回数量（默认 20，最大 100） |

**响应** (200):

```json
{
  "total": 50,
  "items": [
    {
      "id": "uuid",
      "type": "system",
      "title": "系统通知",
      "content": "通知内容",
      "action_url": "https://example.com | null",
      "priority": 0,
      "created_by": "uuid | null",
      "created_at": "ISO8601 datetime",
      "expires_at": "ISO8601 datetime | null"
    }
  ]
}
```

---

### 3. 获取站内信详情（管理端）

**Endpoint**: `GET /api/v1/admin/notifications/{notification_id}`

**描述**: 获取指定站内信的详细信息

**请求头**:

```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| notification_id | string | 站内信 ID |

**响应** (200):

```json
{
  "id": "uuid",
  "type": "system",
  "title": "系统通知",
  "content": "通知内容",
  "action_url": "https://example.com | null",
  "priority": 0,
  "created_by": "uuid | null",
  "created_at": "ISO8601 datetime",
  "expires_at": "ISO8601 datetime | null"
}
```

---

### 4. 更新站内信

**Endpoint**: `PUT /api/v1/admin/notifications/{notification_id}`

**描述**: 更新站内信内容（仅更新内容，不影响已发送的用户记录）

**请求头**:

```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| notification_id | string | 站内信 ID |

**请求体** (所有字段可选):

```json
{
  "type": "system",
  "title": "string",
  "content": "string",
  "action_url": "string | null",
  "priority": 0,
  "expires_at": "ISO8601 datetime | null"
}
```

**响应** (200):

```json
{
  "id": "uuid",
  "type": "system",
  "title": "系统通知",
  "content": "通知内容",
  "action_url": "https://example.com | null",
  "priority": 0,
  "created_by": "uuid | null",
  "created_at": "ISO8601 datetime",
  "expires_at": "ISO8601 datetime | null"
}
```

---

### 5. 删除站内信

**Endpoint**: `DELETE /api/v1/admin/notifications/{notification_id}`

**描述**: 删除站内信（会同时删除所有用户的站内信记录）

**请求头**:

```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| notification_id | string | 站内信 ID |

**响应** (204): 无内容

---

### 6. 发送站内信给用户

**Endpoint**: `POST /api/v1/admin/notifications/{notification_id}/send`

**描述**: 将站内信发送给指定用户或所有用户

**请求头**:

```
Authorization: Bearer <access_token>
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| notification_id | string | 站内信 ID |

**请求体**:

```json
{
  "user_ids": ["uuid-1", "uuid-2"],
  "send_to_all": false
}
```

**字段说明**:

- **user_ids**: 用户 ID 列表（当 send_to_all=false 时使用）
- **send_to_all**: 是否发送给所有用户（如果为 true，则忽略 user_ids）

**响应** (200):

```json
{
  "message": "成功发送给 100 个用户"
}
```

---

## 使用流程示例

### 典型的站内信发送流程

1. **管理员登录**

```bash
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin123"
}
```

2. **创建站内信**

```bash
POST /api/v1/admin/notifications
Authorization: Bearer <admin_token>
{
  "type": "announcement",
  "title": "系统维护通知",
  "content": "系统将于今晚 22:00 进行维护",
  "priority": 1
}
```

3. **发送站内信给用户**

```bash
POST /api/v1/admin/notifications/{notification_id}/send
Authorization: Bearer <admin_token>
{
  "send_to_all": true
}
```

4. **用户接收站内信**

```bash
GET /api/v1/notifications
Authorization: Bearer <user_token>
```

5. **用户标记已读**

```bash
POST /api/v1/notifications/{record_id}/read
Authorization: Bearer <user_token>
```

---

## 注意事项

1. **Token 管理**
   - Access Token 有效期较短（15 分钟），需要定期使用 Refresh Token 刷新
   - 客户端应安全存储 Token，避免 XSS 攻击

2. **站内信发送**
   - 创建站内信后不会自动发送，需要调用发送接口
   - 发送给用户时会自动去重（同一用户不会收到重复的站内信）

3. **分页查询**
   - 建议使用合理的 page_size（20-50）以优化性能
   - 可以结合筛选条件（is_read、notification_type）进行精确查询

4. **删除操作**
   - 管理端删除站内信会同时删除所有用户的站内信记录
   - 用户端删除是软删除，不会物理删除数据

5. **时间格式**
   - 所有时间字段使用 ISO8601 格式
   - 时区为 UTC

---

## 相关文档

- [数据库设计文档](./database-schema.md)
- [站内信类型说明](./notification-types.md)
- [README](../README.md)
