# 即时通讯（IM）系统设计方案

## 概述

本文档详细描述了即时通讯（IM）系统的设计方案，包括 WebSocket 协议、数据库设计、好友关系管理等。

**注意**: 本方案为未来实现预留，当前版本仅实现了站内信系统（REST API）。

---

## 一、系统架构

### 1.1 整体架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  WebSocket  │────▶│   FastAPI   │
│  (Browser)  │◀────│   Server    │◀────│   Backend   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │    Redis    │
                     │  (Online    │
                     │   Status)   │
                     └─────────────┘
```

### 1.2 技术选型

| 组件        | 技术选型                | 说明                 |
| --------- | ------------------- | ------------------ |
| WebSocket | `fastapi.WebSocket` | FastAPI 原生支持       |
| 连接管理      | 内存 + Redis          | 单机内存管理，Redis 支持分布式 |
| 在线状态      | Redis Set           | 存储在线用户列表           |
| 消息存储      | PostgreSQL          | 持久化聊天消息            |
| 心跳机制      | 定时 Ping/Pong        | 30 秒间隔             |

---

## 二、WebSocket 协议设计

### 2.1 连接与认证流程

```
1. 客户端建立 WebSocket 连接：ws://api.com/ws/chat

2. 服务端接受连接，等待认证（5秒超时）

3. 客户端发送认证消息：
   {
     "type": "auth",
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   }

4. 服务端验证 token：
   - 成功：{"type": "auth", "status": "success", "data": {"user_id": "..."}}
   - 失败：关闭连接（code 1008）

5. 认证成功后，开始正常通信
```

### 2.2 消息格式规范

#### 客户端 → 服务端

##### 认证消息

```json
{
  "type": "auth",
  "token": "JWT_TOKEN"
}
```

##### 发送聊天消息

```json
{
  "type": "chat",
  "action": "send",
  "data": {
    "temp_id": "client_temp_id",
    "receiver_id": "uuid",
    "message_type": "text",
    "content": "你好"
  }
}
```

##### 心跳

```json
{"type": "ping"}
```

##### 在线状态变更

```json
{
  "type": "status",
  "data": {"status": "online"}
}
```

##### 正在输入

```json
{
  "type": "typing",
  "data": {"receiver_id": "uuid", "is_typing": true}
}
```

#### 服务端 → 客户端

##### 认证响应

```json
{
  "type": "auth",
  "status": "success",
  "data": {"user_id": "uuid", "username": "张三"}
}
```

##### 新消息通知

```json
{
  "type": "chat",
  "action": "new_message",
  "data": {
    "message_id": "uuid",
    "sender_id": "uuid",
    "sender_name": "张三",
    "message_type": "text",
    "content": "你好",
    "created_at": "2025-02-07T10:30:00Z"
  }
}
```

##### 消息发送确认

```json
{
  "type": "chat",
  "action": "message_sent",
  "data": {
    "temp_id": "client_temp_id",
    "message_id": "server_uuid"
  }
}
```

##### 站内信推送

```json
{
  "type": "notification",
  "data": {
    "notification_id": "uuid",
    "type": "system",
    "title": "系统通知",
    "content": "您有新的系统消息"
  }
}
```

##### 心跳响应

```json
{"type": "pong"}
```

##### 在线状态通知

```json
{
  "type": "status",
  "data": {"user_id": "uuid", "status": "online"}
}
```

##### 正在输入通知

```json
{
  "type": "typing",
  "data": {"user_id": "uuid", "is_typing": true}
}
```

---

## 三、心跳机制

### 3.1 心跳规则

- 客户端每 **30 秒** 发送 `{"type": "ping"}`
- 服务端立即响应 `{"type": "pong"}`
- 服务端 **45 秒**未收到 ping，则关闭连接
- 客户端 **10 秒**未收到 pong，则尝试重连

### 3.2 实现示例

```python
# app/websocket/manager.py

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.last_ping: dict[str, datetime] = {}

    async def ping_timeout_checker(self):
        """检查超时连接"""
        while True:
            await asyncio.sleep(10)
            now = datetime.utcnow()
            timeout_users = [
                user_id
                for user_id, last_ping in self.last_ping.items()
                if (now - last_ping).total_seconds() > 45
            ]
            for user_id in timeout_users:
                await self.disconnect(user_id)
```

---

## 四、重连策略

### 4.1 重连规则

| 重连次数     | 等待时间       |
| -------- | ---------- |
| 第 1 次    | 立即重连       |
| 第 2 次    | 2 秒后       |
| 第 3 次    | 5 秒后       |
| 第 4 次    | 10 秒后      |
| 第 5 次及以后 | 每 30 秒重连一次 |

### 4.2 实现示例（客户端）

```javascript
class WebSocketClient {
  reconnectAttempts = 0;
  maxReconnectAttempts = Infinity;

  reconnect() {
    const delays = [0, 2000, 5000, 10000, 30000];
    const delay = delays[Math.min(this.reconnectAttempts, delays.length - 1)];

    setTimeout(() => {
      this.connect();
      this.reconnectAttempts++;
    }, delay);
  }
}
```

---

## 五、数据库设计

### 5.1 好友关系表 (friendships)

```sql
CREATE TABLE friendships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    friend_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, blocked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(user_id, friend_id),
    CHECK (user_id != friend_id)
);

CREATE INDEX idx_friendships_user_id ON friendships(user_id);
CREATE INDEX idx_friendships_friend_id ON friendships(friend_id);
CREATE INDEX idx_friendships_status ON friendships(status);
```

**字段说明**:

| 字段         | 类型          | 说明    |
| ---------- | ----------- | ----- |
| id         | UUID        | 主键    |
| user_id    | UUID        | 用户 ID |
| friend_id  | UUID        | 好友 ID |
| status     | VARCHAR(20) | 关系状态  |
| created_at | TIMESTAMP   | 创建时间  |
| updated_at | TIMESTAMP   | 更新时间  |

**关系状态**:

- `pending`: 待确认（已发送好友请求）
- `accepted`: 已接受（已是好友）
- `blocked`: 已拉黑

**注意**: 需要创建两条记录（A → B 和 B → A）来表示双向关系。

### 5.2 聊天消息表 (chat_messages)

```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'text', -- text, image, file, voice
    content TEXT NOT NULL,
    file_url VARCHAR(500), -- 文件/图片 URL
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_chat_messages_sender_id ON chat_messages(sender_id);
CREATE INDEX idx_chat_messages_receiver_id ON chat_messages(receiver_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX idx_chat_messages_conversation ON chat_messages(
    LEAST(sender_id, receiver_id),
    GREATEST(sender_id, receiver_id),
    created_at DESC
);
```

**字段说明**:

| 字段           | 类型           | 说明         |
| ------------ | ------------ | ---------- |
| id           | UUID         | 主键         |
| sender_id    | UUID         | 发送者 ID     |
| receiver_id  | UUID         | 接收者 ID     |
| message_type | VARCHAR(20)  | 消息类型       |
| content      | TEXT         | 消息内容       |
| file_url     | VARCHAR(500) | 文件 URL（可选） |
| is_read      | BOOLEAN      | 是否已读       |
| read_at      | TIMESTAMP    | 阅读时间       |
| is_deleted   | BOOLEAN      | 是否已删除      |
| deleted_at   | TIMESTAMP    | 删除时间       |
| created_at   | TIMESTAMP    | 创建时间       |

**消息类型**:

- `text`: 文本消息
- `image`: 图片消息
- `file`: 文件消息
- `voice`: 语音消息

### 5.3 群组表 (groups)

```sql
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_members INTEGER DEFAULT 500,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_groups_owner_id ON groups(owner_id);
```

### 5.4 群组成员表 (group_members)

```sql
CREATE TABLE group_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- owner, admin, member
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(group_id, user_id)
);

CREATE INDEX idx_group_members_group_id ON group_members(group_id);
CREATE INDEX idx_group_members_user_id ON group_members(user_id);
```

### 5.5 群组消息表 (group_messages)

```sql
CREATE TABLE group_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    file_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_group_messages_group_id ON group_messages(group_id);
CREATE INDEX idx_group_messages_created_at ON group_messages(created_at DESC);
```

---

## 六、WebSocket 连接管理器

### 6.1 设计思路

```python
# app/websocket/manager.py

from typing import Dict
from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        # 存储用户 WebSocket 连接: {user_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # 存储用户最后心跳时间: {user_id: datetime}
        self.last_ping: Dict[str, datetime] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """建立连接"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.last_ping[user_id] = datetime.utcnow()

        # 更新 Redis 在线状态
        await redis_client.sadd("online:users", user_id)

    async def disconnect(self, user_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.last_ping:
            del self.last_ping[user_id]

        # 更新 Redis 在线状态
        await redis_client.srem("online:users", user_id)

    async def send_personal_message(self, message: dict, user_id: str):
        """发送私聊消息"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """广播消息（群聊）"""
        for connection in self.active_connections.values():
            await connection.send_json(message)

    def is_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self.active_connections

    async def get_online_users(self) -> list:
        """获取所有在线用户"""
        return await redis_client.smembers("online:users")
```

---

## 七、WebSocket 消息处理器

### 7.1 处理器设计

```python
# app/websocket/handlers.py

async def handle_auth(websocket: WebSocket, token: str) -> dict | None:
    """处理认证消息"""
    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return None

    user_id = payload.get("user_id")
    await websocket.send_json({
        "type": "auth",
        "status": "success",
        "data": {"user_id": user_id}
    })
    return payload

async def handle_chat(
    websocket: WebSocket,
    action: str,
    data: dict,
    user_id: str,
    db: Session
):
    """处理聊天消息"""
    if action == "send":
        # 保存消息到数据库
        message = ChatMessage(
            sender_id=user_id,
            receiver_id=data["receiver_id"],
            message_type=data["message_type"],
            content=data["content"]
        )
        db.add(message)
        db.commit()

        # 发送给接收者（如果在线）
        if manager.is_online(data["receiver_id"]):
            await manager.send_personal_message({
                "type": "chat",
                "action": "new_message",
                "data": {
                    "message_id": str(message.id),
                    "sender_id": user_id,
                    "content": data["content"],
                    "created_at": message.created_at.isoformat()
                }
            }, data["receiver_id"])

        # 发送确认给发送者
        await websocket.send_json({
            "type": "chat",
            "action": "message_sent",
            "data": {
                "temp_id": data["temp_id"],
                "message_id": str(message.id)
            }
        })

async def handle_ping(websocket: WebSocket, user_id: str):
    """处理心跳"""
    manager.last_ping[user_id] = datetime.utcnow()
    await websocket.send_json({"type": "pong"})

async def handle_typing(data: dict, user_id: str):
    """处理正在输入状态"""
    receiver_id = data["receiver_id"]
    if manager.is_online(receiver_id):
        await manager.send_personal_message({
            "type": "typing",
            "data": {"user_id": user_id, "is_typing": data["is_typing"]}
        }, receiver_id)
```

---

## 八、WebSocket 端点实现

### 8.1 FastAPI WebSocket 路由

```python
# app/api/v1/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.websocket.manager import manager
from app.websocket.handlers import (
    handle_auth,
    handle_chat,
    handle_ping,
    handle_typing,
)

router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket 聊天端点

    连接流程：
    1. 客户端建立连接
    2. 发送认证消息（5 秒超时）
    3. 认证成功后开始通信
    4. 定时发送心跳（30 秒）
    """
    await websocket.accept()

    user_id = None

    try:
        # 等待认证消息（5 秒超时）
        auth_data = await websocket.receive_json()
        if auth_data.get("type") == "auth":
            user_info = await handle_auth(websocket, auth_data.get("token"))
            if not user_info:
                return
            user_id = user_info["user_id"]

            # 建立连接
            await manager.connect(user_id, websocket)

            # 消息循环
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "chat":
                    await handle_chat(
                        websocket,
                        data.get("action"),
                        data.get("data"),
                        user_id,
                        db
                    )
                elif msg_type == "ping":
                    await handle_ping(websocket, user_id)
                elif msg_type == "typing":
                    await handle_typing(data.get("data"), user_id)

    except WebSocketDisconnect:
        if user_id:
            await manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if user_id:
            await manager.disconnect(user_id)
```

---

## 九、API 端点设计（REST）

### 9.1 好友关系 API

| 方法     | 路径                          | 说明         |
| ------ | --------------------------- | ---------- |
| POST   | /api/v1/friends/request     | 发送好友请求     |
| POST   | /api/v1/friends/{id}/accept | 接受好友请求     |
| POST   | /api/v1/friends/{id}/reject | 拒绝好友请求     |
| DELETE | /api/v1/friends/{id}        | 删除好友       |
| GET    | /api/v1/friends             | 获取好友列表     |
| GET    | /api/v1/friends/pending     | 获取待处理的好友请求 |

### 9.2 聊天消息 API

| 方法     | 路径                            | 说明          |
| ------ | ----------------------------- | ----------- |
| GET    | /api/v1/messages/{user_id}    | 获取与某用户的聊天记录 |
| POST   | /api/v1/messages/{user_id}    | 发送消息（离线时使用） |
| POST   | /api/v1/messages/{id}/read    | 标记消息为已读     |
| GET    | /api/v1/messages/unread-count | 获取未读消息数量    |
| DELETE | /api/v1/messages/{id}         | 删除消息        |

### 9.3 群组 API

| 方法     | 路径                                    | 说明       |
| ------ | ------------------------------------- | -------- |
| POST   | /api/v1/groups                        | 创建群组     |
| GET    | /api/v1/groups                        | 获取群组列表   |
| GET    | /api/v1/groups/{id}                   | 获取群组详情   |
| PUT    | /api/v1/groups/{id}                   | 更新群组信息   |
| DELETE | /api/v1/groups/{id}                   | 解散群组     |
| POST   | /api/v1/groups/{id}/members           | 添加群成员    |
| DELETE | /api/v1/groups/{id}/members/{user_id} | 移除群成员    |
| GET    | /api/v1/groups/{id}/messages          | 获取群组消息记录 |

---

## 十、在线状态管理

### 10.1 Redis 数据结构

```
# 在线用户集合
Key: online:users
Type: Set
Value: [user_id_1, user_id_2, ...]

# 用户连接信息
Key: user:connections:{user_id}
Type: List
Value: [connection_id_1, connection_id_2, ...]

# 用户最后心跳时间
Key: user:last_ping:{user_id}
Type: String (Unix Timestamp)
Value: 1707260000
```

### 10.2 查询在线状态

```python
async def get_online_status(user_ids: list[str]) -> dict[str, bool]:
    """批量获取用户在线状态"""
    online_users = await redis_client.smembers("online:users")
    return {
        user_id: user_id in online_users
        for user_id in user_ids
    }
```

---

## 十一、安全考虑

### 11.1 认证与授权

- **WebSocket 认证**: 使用 JWT Token，连接后 5 秒内必须认证
- **消息验证**: 验证发送者身份，防止伪造消息
- **权限控制**: 好友关系验证、群组成员验证

### 11.2 防止滥用

- **消息频率限制**: 每秒最多发送 10 条消息
- **连接数限制**: 每个用户最多 3 个并发连接
- **好友请求限制**: 每小时最多发送 20 个好友请求

### 11.3 数据加密

- **传输加密**: 使用 WSS（WebSocket Secure）
- **存储加密**: 敏感消息可考虑端到端加密

---

## 十二、性能优化

### 12.1 消息分发优化

```python
# 使用消息队列异步处理大批量消息
from celery import Celery

celery_app = Celery('im', broker='redis://localhost:6379/0')

@celery_app.task
def send_message_to_offline_users(message: dict, user_ids: list):
    """发送消息给离线用户（推送通知、邮件等）"""
    for user_id in user_ids:
        # 发送推送通知
        send_push_notification(user_id, message)
```

### 12.2 数据库查询优化

- 使用索引优化查询
- 分页加载历史消息
- 缓存常用查询结果（Redis）

---

## 十三、实施步骤

### Phase 1: WebSocket 基础（必须）

- [ ] 实现 WebSocket 连接管理器
- [ ] 实现认证流程
- [ ] 实现心跳机制
- [ ] 实现重连策略

### Phase 2: 好友系统（必须）

- [ ] 创建好友关系表
- [ ] 实现好友请求 API
- [ ] 实现好友列表 API
- [ ] 实现在线状态查询

### Phase 3: 单聊功能（必须）

- [ ] 创建聊天消息表
- [ ] 实现发送/接收消息
- [ ] 实现消息已读状态
- [ ] 实现历史消息查询
- [ ] 实现正在输入状态

### Phase 4: 群聊功能（可选）

- [ ] 创建群组相关表
- [ ] 实现群组管理 API
- [ ] 实现群组消息
- [ ] 实现群组成员管理

### Phase 5: 高级功能（可选）

- [ ] 文件上传/分享
- [ ] 语音消息
- [ ] 消息搜索
- [ ] 端到端加密

---

## 十四、测试验证

### 14.1 WebSocket 连接测试

```bash
# 使用 wscat 测试 WebSocket
wscat -c "ws://localhost:8000/api/v1/ws/chat"

# 发送认证消息
{"type":"auth","token":"YOUR_JWT_TOKEN"}

# 发送心跳
{"type":"ping"}

# 发送消息
{"type":"chat","action":"send","data":{"temp_id":"123","receiver_id":"USER_ID","message_type":"text","content":"你好"}}
```

### 14.2 功能验证

1. **连接测试**: 多用户同时连接、断线重连
2. **消息测试**: 发送/接收消息、离线消息、已读状态
3. **性能测试**: 1000+ 并发连接、消息吞吐量
4. **安全测试**: 未授权访问、消息伪造、频率限制

---

## 十五、相关文档

- [API 文档](./api-documentation.md)

- [数据库设计文档](./database-schema.md)

- [站内信类型说明](./notification-types.md)

- [README](../README.md)

- [API 文档](./api-documentation.md)

- [数据库设计文档](./database-schema.md)

- [站内信类型说明](./notification-types.md)

- [README](../README.md)
