## 站中信

### 接口使用指南

#### P0 接口

管理员创建站中信：POST /api/v1/admin/notifications

管理员发送站内信给用户：POST /api/v1/admin/notifications/{notification_id}/send

用户获取当前的站内信列表：GET /api/v1/notifications

用户获取站内信详情：GET /api/v1/notifications/{record_id}

管理员获取站内信列表：GET /api/v1/admin/notifications

管理员获取站内信详情：GET /api/v1/admin/notifications/{notification_id}

> 依旧是基础的 create、delete、update、get、list 与相关的数据库表...
>
> web 后端开发只能如此吗？看样子 im 即时通讯才算是更高一级吧...