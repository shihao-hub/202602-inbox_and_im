"""
用户删除站内信场景测试

这个场景模拟了用户删除站内信的完整流程。
"""

import pytest


def test_user_delete_single_notification(client, auth_headers, db_session, test_user):
    """
    场景：用户删除单条站内信
    =======================
    1. 用户有 3 条站内信
    2. 删除其中 1 条
    3. 验证站内信总数减少
    4. 验证被删除的站内信不再出现在列表中
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin8",
        email="admin8@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 3 条站内信
    for i in range(3):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"通知 {i+1}",
            content=f"内容 {i+1}",
            priority=0,
            created_by=admin.id,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=False,
        )
        db_session.add(record)
        db_session.commit()

    # 验证初始有 3 条站内信
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3

    # 获取第一条站内信的 record_id
    record_to_delete = data["items"][0]["id"]

    # 删除第一条站内信
    response = client.delete(
        f"/api/v1/notifications/{record_to_delete}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # 验证站内信总数变为 2
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2

    # 验证被删除的站内信不再出现在列表中
    record_ids = [item["id"] for item in data["items"]]
    assert record_to_delete not in record_ids


def test_user_delete_multiple_notifications(client, auth_headers, db_session, test_user):
    """
    场景：用户删除多条站内信
    =======================
    1. 用户有 5 条站内信
    2. 逐条删除 3 条
    3. 验证剩余 2 条
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin9",
        email="admin9@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 5 条站内信
    for i in range(5):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"通知 {i+1}",
            content=f"内容 {i+1}",
            priority=0,
            created_by=admin.id,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=False,
        )
        db_session.add(record)
        db_session.commit()

    # 验证初始有 5 条站内信
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.json()["total"] == 5

    # 删除 3 条站内信
    response = client.get("/api/v1/notifications", headers=auth_headers)
    record_ids = [item["id"] for item in response.json()["items"][:3]]

    for record_id in record_ids:
        response = client.delete(
            f"/api/v1/notifications/{record_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    # 验证剩余 2 条
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.json()["total"] == 2


def test_user_delete_all_notifications(client, auth_headers, db_session, test_user):
    """
    场景：用户删除所有站内信
    =======================
    1. 用户有多条站内信
    2. 逐条删除所有站内信
    3. 验证站内信列表为空
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin10",
        email="admin10@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 5 条站内信
    for i in range(5):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"通知 {i+1}",
            content=f"内容 {i+1}",
            priority=0,
            created_by=admin.id,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=False,
        )
        db_session.add(record)
        db_session.commit()

    # 删除所有站内信
    response = client.get("/api/v1/notifications", headers=auth_headers)
    record_ids = [item["id"] for item in response.json()["items"]]

    for record_id in record_ids:
        response = client.delete(
            f"/api/v1/notifications/{record_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    # 验证站内信列表为空
    response = client.get("/api/v1/notifications", headers=auth_headers)
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_user_delete_nonexistent_notification(client, auth_headers):
    """
    场景：用户尝试删除不存在的站内信
    ===============================
    1. 使用不存在的 record_id
    2. 尝试删除
    3. 验证返回 404 错误
    """
    fake_record_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(
        f"/api/v1/notifications/{fake_record_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_user_delete_notification_without_auth(client):
    """
    场景：未登录用户尝试删除站内信
    =============================
    1. 不提供 token
    2. 尝试删除站内信
    3. 验证返回 403 错误
    """
    response = client.delete("/api/v1/notifications/some-id")
    assert response.status_code == 403


def test_user_delete_read_and_unread_notifications(client, auth_headers, db_session, test_user):
    """
    场景：用户删除已读和未读的站内信
    =============================
    1. 用户有 2 条已读，2 条未读
    2. 删除 1 条已读和 1 条未读
    3. 验证剩余 1 条已读和 1 条未读
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash
    from datetime import datetime

    # 创建管理员
    admin = User(
        username="admin11",
        email="admin11@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 2 条已读站内信
    for i in range(2):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"已读通知 {i+1}",
            content=f"已读 {i+1}",
            priority=0,
            created_by=admin.id,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=True,
            read_at=datetime.now(),
        )
        db_session.add(record)
        db_session.commit()

    # 创建 2 条未读站内信
    for i in range(2):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"未读通知 {i+1}",
            content=f"未读 {i+1}",
            priority=0,
            created_by=admin.id,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=False,
        )
        db_session.add(record)
        db_session.commit()

    # 获取站内信列表
    response = client.get("/api/v1/notifications", headers=auth_headers)
    items = response.json()["items"]

    # 找到 1 条已读和 1 条未读的 record_id
    read_record_id = None
    unread_record_id = None
    for item in items:
        if item["is_read"] and read_record_id is None:
            read_record_id = item["id"]
        elif not item["is_read"] and unread_record_id is None:
            unread_record_id = item["id"]

    # 删除 1 条已读
    response = client.delete(
        f"/api/v1/notifications/{read_record_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # 删除 1 条未读
    response = client.delete(
        f"/api/v1/notifications/{unread_record_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # 验证剩余 1 条已读和 1 条未读
    response = client.get("/api/v1/notifications", headers=auth_headers)
    data = response.json()
    assert data["total"] == 2

    read_count = sum(1 for item in data["items"] if item["is_read"])
    unread_count = sum(1 for item in data["items"] if not item["is_read"])
    assert read_count == 1
    assert unread_count == 1


def test_user_delete_then_receive_new_notifications(client, auth_headers, db_session, test_user):
    """
    场景：用户删除站内信后接收新站内信
    =============================
    1. 用户有站内信，全部删除
    2. 管理员发送新站内信
    3. 验证用户能收到新站内信
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin12",
        email="admin12@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 3 条站内信
    for i in range(3):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"通知 {i+1}",
            content=f"内容 {i+1}",
            priority=0,
            created_by=admin.id,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=False,
        )
        db_session.add(record)
        db_session.commit()

    # 删除所有站内信
    response = client.get("/api/v1/notifications", headers=auth_headers)
    record_ids = [item["id"] for item in response.json()["items"]]

    for record_id in record_ids:
        client.delete(f"/api/v1/notifications/{record_id}", headers=auth_headers)

    # 验证站内信列表为空
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.json()["total"] == 0

    # 管理员发送新站内信
    notification = Notification(
        type=NotificationType.SYSTEM,
        title="新通知",
        content="这是新发送的通知",
        priority=0,
        created_by=admin.id,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    record = NotificationRecord(
        notification_id=notification.id,
        user_id=test_user.id,
        is_read=False,
    )
    db_session.add(record)
    db_session.commit()

    # 验证用户能收到新站内信
    response = client.get("/api/v1/notifications", headers=auth_headers)
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["notification"]["title"] == "新通知"
