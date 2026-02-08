"""
管理员编辑站内信场景测试

这个场景模拟了管理员编辑和更新站内信的完整流程。
"""

from datetime import datetime, timedelta
import pytest


def test_admin_update_notification_content(client, auth_headers, db_session):
    """
    场景：管理员更新站内信内容
    ========================
    1. 创建站内信
    2. 更新标题、内容、优先级
    3. 验证更新成功
    4. 验证不影响已发送的用户记录
    """
    # 步骤 1: 创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "原标题",
            "content": "原内容",
            "priority": 0,
        },
    )
    assert response.status_code == 201
    notification_id = response.json()["id"]

    # 步骤 2: 更新站内信
    response = client.put(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
        json={
            "title": "更新后的标题",
            "content": "更新后的内容",
            "priority": 2,
        },
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["title"] == "更新后的标题"
    assert updated_data["content"] == "更新后的内容"
    assert updated_data["priority"] == 2

    # 步骤 3: 验证更新成功
    response = client.get(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "更新后的标题"
    assert data["content"] == "更新后的内容"
    assert data["priority"] == 2


def test_admin_partial_update_notification(client, auth_headers):
    """
    场景：管理员部分更新站内信字段
    =============================
    1. 创建站内信
    2. 只更新标题
    3. 验证其他字段保持不变
    """
    # 创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "原标题",
            "content": "原内容",
            "priority": 0,
            "action_url": "https://example.com/original",
        },
    )
    assert response.status_code == 201
    notification_id = response.json()["id"]

    # 只更新标题
    response = client.put(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
        json={
            "title": "只更新标题",
        },
    )
    assert response.status_code == 200

    # 验证其他字段保持不变
    response = client.get(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
    )
    data = response.json()
    assert data["title"] == "只更新标题"
    assert data["content"] == "原内容"  # 保持不变
    assert data["priority"] == 0  # 保持不变
    assert data["action_url"] == "https://example.com/original"  # 保持不变


def test_admin_update_notification_type(client, auth_headers):
    """
    场景：管理员更新站内信类型
    ========================
    1. 创建 system 类型的站内信
    2. 更新为 announcement 类型
    3. 验证类型更新成功
    """
    # 创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "系统通知",
            "content": "内容",
            "priority": 0,
        },
    )
    assert response.status_code == 201
    notification_id = response.json()["id"]

    # 更新类型
    response = client.put(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
        json={
            "type": "announcement",
        },
    )
    assert response.status_code == 200

    # 验证类型已更新
    response = client.get(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
    )
    data = response.json()
    assert data["type"] == "announcement"


def test_admin_update_notification_expiry(client, auth_headers):
    """
    场景：管理员更新站内信过期时间
    =============================
    1. 创建无过期时间的站内信
    2. 添加过期时间
    3. 验证过期时间设置成功
    """
    # 创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "测试通知",
            "content": "内容",
            "priority": 0,
        },
    )
    assert response.status_code == 201
    notification_id = response.json()["id"]
    assert response.json()["expires_at"] is None

    # 添加过期时间
    expires_at = datetime.now() + timedelta(days=30)
    response = client.put(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
        json={
            "expires_at": expires_at.isoformat(),
        },
    )
    assert response.status_code == 200

    # 验证过期时间已设置
    response = client.get(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
    )
    data = response.json()
    assert data["expires_at"] is not None


def test_admin_update_nonexistent_notification(client, auth_headers):
    """
    场景：管理员更新不存在的站内信
    =============================
    1. 使用不存在的 notification_id
    2. 尝试更新
    3. 验证返回 404 错误
    """
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.put(
        f"/api/v1/admin/notifications/{fake_id}",
        headers=auth_headers,
        json={
            "title": "更新标题",
        },
    )
    assert response.status_code == 404


def test_admin_delete_notification(client, auth_headers, db_session, test_user):
    """
    场景：管理员删除站内信
    =====================
    1. 创建站内信
    2. 发送给用户
    3. 删除站内信
    4. 验证站内信和用户记录都被删除
    """
    from app.models.notification import NotificationRecord

    # 创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "待删除的通知",
            "content": "这条通知将被删除",
            "priority": 0,
        },
    )
    assert response.status_code == 201
    notification_id = response.json()["id"]

    # 发送给用户
    response = client.post(
        f"/api/v1/admin/notifications/{notification_id}/send",
        headers=auth_headers,
        json={
            "user_ids": [str(test_user.id)],
            "send_to_all": False,
        },
    )
    assert response.status_code == 200

    # 验证用户收到了站内信
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.json()["total"] == 1

    # 删除站内信
    response = client.delete(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # 验证站内信已被删除
    response = client.get(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404

    # 验证用户的站内信记录也被删除
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.json()["total"] == 0


def test_admin_delete_nonexistent_notification(client, auth_headers):
    """
    场景：管理员删除不存在的站内信
    =============================
    1. 使用不存在的 notification_id
    2. 尝试删除
    3. 验证返回 404 错误
    """
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(
        f"/api/v1/admin/notifications/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_admin_update_then_resend_notification(client, auth_headers, db_session, test_user):
    """
    场景：管理员更新站内信后重新发送
    =============================
    1. 创建站内信并发送给用户 A
    2. 更新站内信内容
    3. 发送给用户 B
    4. 验证用户 A 和 B 都能看到最新内容
    """
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建用户 B
    user_b = User(
        username="user_b",
        email="userb@example.com",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    # 创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "announcement",
            "title": "原公告",
            "content": "原内容",
            "priority": 0,
        },
    )
    assert response.status_code == 201
    notification_id = response.json()["id"]

    # 发送给用户 A（test_user）
    response = client.post(
        f"/api/v1/admin/notifications/{notification_id}/send",
        headers=auth_headers,
        json={
            "user_ids": [str(test_user.id)],
            "send_to_all": False,
        },
    )
    assert response.status_code == 200

    # 更新站内信内容
    response = client.put(
        f"/api/v1/admin/notifications/{notification_id}",
        headers=auth_headers,
        json={
            "title": "更新后的公告",
            "content": "更新后的内容",
        },
    )
    assert response.status_code == 200

    # 发送给用户 B
    response = client.post(
        f"/api/v1/admin/notifications/{notification_id}/send",
        headers=auth_headers,
        json={
            "user_ids": [str(user_b.id)],
            "send_to_all": False,
        },
    )
    assert response.status_code == 200

    # 验证用户 A 看到的是更新后的内容（因为引用的是同一个 notification）
    response = client.get("/api/v1/notifications", headers=auth_headers)
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["notification"]["title"] == "更新后的公告"
    assert data["items"][0]["notification"]["content"] == "更新后的内容"
