"""
用户批量管理站内信场景测试

这个场景模拟了用户批量标记已读、批量删除等操作。
"""

import pytest


def test_user_mark_all_as_read_flow(client, auth_headers, db_session, test_user):
    """
    场景：用户批量将所有站内信标记为已读
    ====================================
    1. 用户有 5 条未读站内信
    2. 查看未读数量为 5
    3. 执行"全部标记已读"操作
    4. 验证所有站内信已标记为已读
    5. 验证未读数量变为 0
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin4",
        email="admin4@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 5 条未读站内信
    for i in range(5):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"未读通知 {i+1}",
            content=f"这是第 {i+1} 条未读通知",
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

    # 验证初始状态：5 条未读
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    count_data = response.json()
    assert count_data["unread_count"] == 5

    # 执行"全部标记已读"
    response = client.post("/api/v1/notifications/read-all", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "已将 5 条站内信标记为已读" in result["message"]

    # 验证未读数量变为 0
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    count_data = response.json()
    assert count_data["unread_count"] == 0

    # 验证所有站内信都已标记为已读
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["unread_count"] == 0

    # 验证每条都是已读状态
    for item in data["items"]:
        assert item["is_read"] is True


def test_user_mark_all_as_read_when_empty(client, auth_headers):
    """
    场景：用户在没有站内信时执行"全部标记已读"
    ================================
    1. 用户没有任何站内信
    2. 执行"全部标记已读"操作
    3. 验证返回正确的消息（标记了 0 条）
    """
    response = client.post("/api/v1/notifications/read-all", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "已将 0 条站内信标记为已读" in result["message"]


def test_user_mark_all_as_read_partial_already_read(client, auth_headers, db_session, test_user):
    """
    场景：用户部分站内信已读，部分未读，执行全部标记已读
    ================================
    1. 用户有 3 条未读，2 条已读
    2. 执行"全部标记已读"
    3. 验证只标记了 3 条未读的
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash
    from datetime import datetime

    # 创建管理员
    admin = User(
        username="admin5",
        email="admin5@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 3 条未读站内信
    for i in range(3):
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

    # 验证初始状态：3 条未读
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    count_data = response.json()
    assert count_data["unread_count"] == 3

    # 执行"全部标记已读"
    response = client.post("/api/v1/notifications/read-all", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "已将 3 条站内信标记为已读" in result["message"]

    # 验证最终状态
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["unread_count"] == 0


def test_user_progressive_reading_flow(client, auth_headers, db_session, test_user):
    """
    场景：用户逐条阅读站内信的流程
    =============================
    1. 用户有 3 条未读站内信
    2. 逐条标记为已读
    3. 验证未读数量逐条递减
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin6",
        email="admin6@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 3 条站内信
    notification_ids = []
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
        notification_ids.append(notification.id)

        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=False,
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

    # 获取所有 record_id
    response = client.get("/api/v1/notifications", headers=auth_headers)
    record_ids = [item["id"] for item in response.json()["items"]]

    # 验证初始未读数量
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.json()["unread_count"] == 3

    # 逐条标记为已读
    for i, record_id in enumerate(record_ids, 1):
        response = client.post(
            f"/api/v1/notifications/{record_id}/read",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # 验证未读数量递减
        response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
        expected_count = 3 - i
        assert response.json()["unread_count"] == expected_count

    # 最终验证所有都已读
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.json()["unread_count"] == 0


def test_user_read_all_and_receive_new_notifications(client, auth_headers, db_session, test_user):
    """
    场景：用户全部标记已读后又收到新站内信
    ================================
    1. 用户有 3 条站内信，全部标记为已读
    2. 管理员发送新站内信
    3. 验证未读数量正确
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin7",
        email="admin7@example.com",
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

    # 全部标记为已读
    response = client.post("/api/v1/notifications/read-all", headers=auth_headers)
    assert response.status_code == 200

    # 验证未读数量为 0
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.json()["unread_count"] == 0

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

    # 验证未读数量为 1
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.json()["unread_count"] == 1
