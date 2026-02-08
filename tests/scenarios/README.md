# 站内信系统测试场景指南

本目录包含基于场景的 pytest 测试用例,每个测试文件代表一个完整的用户行为流程。

## 📁 测试文件说明

### 用户注册登录场景
**文件**: `test_user_registration_and_login.py`

测试用户从注册到登录的完整流程:
- 新用户注册
- 使用用户名或邮箱登录
- 获取和验证 access token
- 用户登出流程
- 重复注册和登录失败场景

### 管理员创建发送站内信场景
**文件**: `test_admin_create_and_send_notification.py`

测试管理员创建和发送站内信的完整流程:
- 创建站内信内容
- 发送给单个用户
- 发送给所有用户
- 创建不同类型的站内信 (system/business/reminder/announcement)
- 设置过期时间和优先级
- 查看站内信列表和详情

### 用户接收阅读站内信场景
**文件**: `test_user_receive_and_read_notifications.py`

测试用户接收和阅读站内信的完整流程:
- 接收站内信
- 查看站内信列表
- 查看站内信详情
- 标记单条站内信为已读
- 使用分页查看站内信

### 用户批量管理站内信场景
**文件**: `test_user_batch_manage_notifications.py`

测试用户批量管理站内信的完整流程:
- 全部标记为已读
- 逐条阅读站内信
- 部分已读时的批量操作
- 标记已读后又收到新站内信

### 管理员编辑站内信场景
**文件**: `test_admin_edit_notifications.py`

测试管理员编辑和删除站内信的完整流程:
- 更新站内信内容
- 部分更新字段
- 更新站内信类型和过期时间
- 删除站内信
- 更新后重新发送

### 用户删除站内信场景
**文件**: `test_user_delete_notifications.py`

测试用户删除站内信的完整流程:
- 删除单条站内信
- 删除多条站内信
- 删除所有站内信
- 删除已读和未读站内信
- 删除后接收新站内信

### 站内信筛选功能场景
**文件**: `test_notification_filtering.py`

测试站内信筛选和分页功能:
- 按已读/未读状态筛选
- 按站内信类型筛选
- 组合筛选条件
- 筛选结果分页
- 无效参数处理

## 🚀 运行测试

### 安装依赖

```bash
# 安装开发依赖
pip install pytest
```

### 运行所有场景测试

```bash
# 在项目根目录运行
pytest tests/scenarios/ -v
```

### 运行特定场景测试

```bash
# 只运行用户注册登录场景
pytest tests/scenarios/test_user_registration_and_login.py -v

# 只运行管理员创建发送站内信场景
pytest tests/scenarios/test_admin_create_and_send_notification.py -v

# 只运行用户接收阅读站内信场景
pytest tests/scenarios/test_user_receive_and_read_notifications.py -v
```

### 运行特定测试用例

```bash
# 运行单个测试用例
pytest tests/scenarios/test_user_registration_and_login.py::test_new_user_complete_registration_flow -v

# 使用 -k 关键字过滤
pytest tests/scenarios/ -k "register" -v
pytest tests/scenarios/ -k "send_notification" -v
```

### 查看测试覆盖率

```bash
# 安装 pytest-cov
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest tests/scenarios/ --cov=app --cov-report=html

# 查看报告
# 打开 htmlcov/index.html
```

### 显示详细输出

```bash
# 显示 print 输出
pytest tests/scenarios/ -v -s

# 显示更详细的信息
pytest tests/scenarios/ -vv
```

### 并行运行测试（加快速度）

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 使用多进程运行
pytest tests/scenarios/ -n auto
```

## 📊 测试结果示例

```
tests/scenarios/test_user_registration_and_login.py::test_new_user_complete_registration_flow PASSED
tests/scenarios/test_user_registration_and_login.py::test_login_with_email_instead_of_username PASSED
tests/scenarios/test_admin_create_and_send_notification.py::test_admin_create_and_send_notification_to_single_user PASSED
tests/scenarios/test_user_receive_and_read_notifications.py::test_user_receive_and_read_notification_flow PASSED

======================== 42 passed in 2.34s ========================
```

## 🛠️ 编写新的测试场景

### 测试文件模板

```python
"""
测试场景描述

这个场景模拟了...
"""

import pytest


def test_scenario_name(client, auth_headers, db_session, test_user):
    """
    场景：场景描述
    =============
    1. 第一步
    2. 第二步
    3. 验证结果
    """
    # 步骤 1: ...
    # 步骤 2: ...
    # 验证: ...
    assert True
```

### 可用的 Fixtures

- `client`: FastAPI 测试客户端
- `db_session`: 数据库会话
- `test_user`: 测试用户
- `auth_headers`: 用户认证头
- `admin_user`: 管理员用户
- `admin_auth_headers`: 管理员认证头
- `multiple_users`: 多个测试用户
- `user_auth_headers`: 多个用户的认证头

### 测试最佳实践

1. **使用描述性的测试函数名**: 清楚说明测试的场景
2. **添加文档字符串**: 详细描述测试步骤
3. **遵循 AAA 模式**: Arrange（准备）→ Act（执行）→ Assert（验证）
4. **使用 fixtures 复用代码**: 避免重复创建用户、登录等
5. **测试边界情况**: 不仅测试正常流程,也要测试错误场景
6. **保持测试独立**: 每个测试应该能够独立运行

## 📝 测试数据说明

### 测试数据库

测试使用 SQLite 内存数据库 (`test.db`),每次测试运行都会:
1. 创建所有表
2. 运行测试
3. 删除所有表

这样可以确保每个测试都在干净的环境中运行。

### 测试用户

默认测试用户:
- 用户名: `testuser`
- 邮箱: `test@example.com`
- 密码: `password123`

管理员用户:
- 用户名: `admin`
- 邮箱: `admin@example.com`
- 密码: `adminpass123`

## 🔗 相关文档

- [API 文档](../../docs/api-design.md)
- [数据库设计](../../docs/database-design.md)
- [项目 README](../../README.md)

## ❓ 常见问题

### Q: 测试失败怎么办?

A: 查看失败信息的详细输出:
```bash
pytest tests/scenarios/ -v --tb=short
```

### Q: 如何调试单个测试?

A: 使用 pdb 调试器:
```bash
pytest tests/scenarios/test_xxx.py::test_func --pdb
```

### Q: 测试太慢怎么办?

A: 使用 pytest-xdist 并行运行:
```bash
pytest tests/scenarios/ -n auto
```

### Q: 如何只运行失败的测试?

A: 使用 --lf (last failed) 选项:
```bash
pytest tests/scenarios/ --lf
```

### Q: 测试数据库在哪里?

A: 测试使用 SQLite 内存数据库,不会影响生产数据库。测试结束后数据库会被删除。

## 📧 联系方式

如有问题,请联系开发团队或提交 Issue。
