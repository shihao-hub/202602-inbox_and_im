# 站内信系统 Bruno 测试集合

这是一套完整的站内信系统 API 测试集合，使用 Bruno 测试工具编写。

## 目录结构

```
inbox_and_im/
├── collection.bru              # 集合配置
├── environments/               # 环境配置
│   └── local.bru              # 本地开发环境
├── auth/                      # 认证测试
│   ├── 01-user-register.bru  # 用户注册
│   ├── 02-user-login.bru     # 用户登录
│   ├── 03-admin-login.bru    # 管理员登录
│   └── 04-get-current-user.bru # 获取当前用户信息
├── admin/                     # 管理端测试
│   ├── 00-send-notification-workflow.bru # 发送通知工作流指南
│   ├── 01-create-notification.bru
│   ├── 02-create-business-notification.bru
│   ├── 03-get-notifications.bru
│   ├── 04-get-notification-detail.bru
│   ├── 05-update-notification.bru
│   ├── 06-send-notification-to-users.bru
│   ├── 07-send-notification-to-all.bru
│   ├── 08-delete-notification.bru
│   └── errors/               # 错误场景测试
│       ├── 01-unauthorized-401.bru
│       ├── 02-not-found-404.bru
│       └── 03-validation-error-400.bru
├── user/                     # 用户端测试
│   ├── 01-get-notifications.bru
│   ├── 02-get-unread-notifications.bru
│   ├── 03-get-read-notifications.bru
│   ├── 04-filter-by-type.bru
│   ├── 05-get-unread-count.bru
│   ├── 06-get-notification-detail.bru
│   ├── 07-mark-as-read.bru
│   ├── 08-mark-all-as-read.bru
│   ├── 09-delete-notification.bru
│   └── errors/              # 错误场景测试
│       ├── 01-unauthorized-401.bru
│       ├── 02-not-found-404.bru
│       └── 03-forbidden-403.bru
└── tests/                    # 集成测试场景
    ├── 01-full-workflow.bru
    └── 02-priority-workflow.bru
```

## 快速开始

### 1. 安装 Bruno

从 [Bruno 官网](https://www.usebruno.com/) 下载并安装 Bruno。

### 2. 配置环境

确保 `environments/local.bru` 中的配置正确：

```properties
vars {
  host: http://127.0.0.1:8000
  baseUrl: http://127.0.0.1:8000
}
```

### 3. 运行测试

#### 完整测试流程

**🚀 快速开始：发送通知工作流**

最简单的方式是运行工作流测试：

1. `admin/00-send-notification-workflow.bru` - 完整工作流指南（会自动注册用户并显示后续步骤）

**📋 手动执行流程**

1. **认证测试**（按顺序执行）：
   - `auth/01-user-register.bru` - 注册测试用户（自动设置 userId 和 userToken）
   - `auth/02-user-login.bru` - 用户登录并获取 token
   - `auth/03-admin-login.bru` - 管理员登录并获取 token
   - `auth/04-get-current-user.bru` - 获取当前用户信息（设置 userId）

2. **管理端测试**（需要管理员 token）：
   - `admin/01-create-notification.bru` - 创建站内信
   - `admin/03-get-notifications.bru` - 获取站内信列表
   - `admin/04-get-notification-detail.bru` - 获取站内信详情
   - `admin/05-update-notification.bru` - 更新站内信
   - `admin/06-send-notification-to-users.bru` - 发送给指定用户
   - `admin/07-send-notification-to-all.bru` - 发送给所有用户
   - `admin/08-delete-notification.bru` - 删除站内信

3. **用户端测试**（需要用户 token）：
   - `user/01-get-notifications.bru` - 获取站内信列表
   - `user/02-get-unread-notifications.bru` - 获取未读站内信
   - `user/03-get-read-notifications.bru` - 获取已读站内信
   - `user/04-filter-by-type.bru` - 按类型筛选
   - `user/05-get-unread-count.bru` - 获取未读数量
   - `user/06-get-notification-detail.bru` - 获取站内信详情
   - `user/07-mark-as-read.bru` - 标记为已读
   - `user/08-mark-all-as-read.bru` - 全部标记已读
   - `user/09-delete-notification.bru` - 删除站内信

#### 单独运行某个测试

在 Bruno 中双击对应的 `.bru` 文件即可运行。

## 测试覆盖的 API

### 管理端 API

| 方法 | 路径 | 测试文件 |
|------|------|---------|
| POST | `/api/v1/admin/notifications` | `admin/01-create-notification.bru` |
| GET | `/api/v1/admin/notifications` | `admin/03-get-notifications.bru` |
| GET | `/api/v1/admin/notifications/{id}` | `admin/04-get-notification-detail.bru` |
| PUT | `/api/v1/admin/notifications/{id}` | `admin/05-update-notification.bru` |
| DELETE | `/api/v1/admin/notifications/{id}` | `admin/08-delete-notification.bru` |
| POST | `/api/v1/admin/notifications/{id}/send` | `admin/06-send-notification-to-users.bru` |

### 用户端 API

| 方法 | 路径 | 测试文件 |
|------|------|---------|
| GET | `/api/v1/notifications` | `user/01-get-notifications.bru` |
| GET | `/api/v1/notifications?is_read=false` | `user/02-get-unread-notifications.bru` |
| GET | `/api/v1/notifications?is_read=true` | `user/03-get-read-notifications.bru` |
| GET | `/api/v1/notifications?notification_type=system` | `user/04-filter-by-type.bru` |
| GET | `/api/v1/notifications/unread-count` | `user/05-get-unread-count.bru` |
| GET | `/api/v1/notifications/{record_id}` | `user/06-get-notification-detail.bru` |
| POST | `/api/v1/notifications/{record_id}/read` | `user/07-mark-as-read.bru` |
| POST | `/api/v1/notifications/read-all` | `user/08-mark-all-as-read.bru` |
| DELETE | `/api/v1/notifications/{record_id}` | `user/09-delete-notification.bru` |

## 变量说明

测试过程中会自动设置以下变量：

| 变量名 | 说明 | 来源 |
|--------|------|------|
| `adminToken` | 管理员 JWT token | `auth/03-admin-login.bru` |
| `userToken` | 普通 JWT token | `auth/01-user-register.bru` 或 `auth/02-user-login.bru` |
| `notificationId` | 站内信 ID | `admin/01-create-notification.bru` |
| `businessNotificationId` | 业务类型站内信 ID | `admin/02-create-business-notification.bru` |
| `notificationRecordId` | 用户站内信记录 ID | `user/01-get-notifications.bru` |
| `userId` | 用户 ID | `auth/01-user-register.bru` 或 `auth/04-get-current-user.bru` |

## 测试场景

### 1. 完整流程测试

测试完整的站内信生命周期：

```
创建站内信 → 发送给用户 → 用户查看 → 标记已读 → 删除站内信
```

参考：`tests/01-full-workflow.bru`

### 2. 优先级测试

测试不同优先级站内信的创建和排序：

- 优先级 0：普通
- 优先级 1：重要
- 优先级 2：紧急

参考：`tests/02-priority-workflow.bru`

### 3. 错误场景测试

测试各种错误场景：

- 未授权访问（401）
- 资源不存在（404）
- 参数验证失败（422）
- 权限不足（403）

参考：`admin/errors/` 和 `user/errors/`

## 编写规范

参考 `bruno-tests` 的实现方式，测试文件遵循以下规范：

### 命名规范

- 文件名使用 `序号-描述 状态码.bru` 格式
- 使用英文描述性名称
- 明确标识预期状态码

### 文件结构

```javascript
meta {
  name: 测试名称
  type: http
  seq: 执行顺序
}

get/post/put/delete {
  url: 请求URL
  body: 请求体类型
  auth: 认证方式
}

headers { ... }

body:json { ... }

script:post-response {
  // 后置脚本
}

tests {
  test("测试描述", function() {
    // 断言
  });
}
```

### 最佳实践

1. **使用环境变量**：通过 `{{变量名}}` 引用环境配置
2. **设置依赖关系**：使用 `script:post-response` 保存变量供后续使用
3. **编写断言**：在 `tests` 中添加测试断言
4. **错误处理**：检查响应状态码，失败时使用 `bru.setNextRequest(false)` 中断流程
5. **日志输出**：使用 `console.log` 输出测试信息

## 扩展测试

如需添加新的测试用例：

1. 在对应目录下创建新的 `.bru` 文件
2. 参考现有测试文件的结构
3. 添加必要的测试断言
4. 更新本 README 文档

## 故障排除

### 常见问题

1. **401 Unauthorized**
   - 检查是否已运行认证测试
   - 确认 token 是否正确设置

2. **404 Not Found**
   - 检查 API 路径是否正确
   - 确认资源 ID 是否存在

3. **userId 模板变量未替换（`{{userId}}`）**
   - 确保已按顺序运行测试：`auth/01-user-register.bru` → `auth/03-admin-login.bru` → `admin/01-create-notification.bru` → `admin/06-send-notification-to-users.bru`
   - 或运行 `admin/00-send-notification-workflow.bru` 获取完整指南
   - 检查控制台是否输出 "✅ User ID saved"

4. **测试失败**
   - 查看控制台输出的错误信息
   - 检查 API 服务是否正常运行

### 调试技巧

- 在 Bruno 的 Console 面板查看日志
- 使用 `console.log()` 输出变量值
- 检查 Response 面板的响应内容
- 使用 ` bru.setNextRequest(false)` 中断测试流程

## 参考资料

- [Bruno 官方文档](https://docs.usebruno.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [项目 README](../../README.md)
