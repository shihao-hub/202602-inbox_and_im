"""
用户接收和阅读站内信场景测试

这个场景模拟了用户接收、查看和阅读站内信的完整流程。
"""

import pytest


def test_user_receive_and_read_notification_flow(client, auth_headers, db_session, test_user):
    """
    场景：用户接收和阅读站内信的完整流程
    =====================================
    1. 用户登录并访问站内信列表
    2. 查看未读数量
    3. 查看站内信详情
    4. 标记为已读
    5. 验证未读数量减少
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.core.security import get_password_hash
    from app.models.user import User
    import uuid

    # 创建一个管理员用户来发送站内信
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    # 创建站内信内容
    notification = Notification(
        type=NotificationType.SYSTEM,
        title="欢迎使用系统",
        content="欢迎您使用我们的站内信系统！",
        priority=1,
        created_by=admin.id,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    # 创建站内信记录（模拟发送）
    record = NotificationRecord(
        notification_id=notification.id,
        user_id=test_user.id,
        is_read=False,
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    # 步骤 1: 用户获取站内信列表
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["unread_count"] == 1
    assert len(data["items"]) == 1

    notification_item = data["items"][0]
    assert notification_item["notification"]["title"] == "欢迎使用系统"
    assert notification_item["is_read"] is False
    record_id = notification_item["id"]

    # 步骤 2: 查看未读数量
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    count_data = response.json()
    assert count_data["unread_count"] == 1

    # 步骤 3: 查看站内信详情
    response = client.get(
        f"/api/v1/notifications/{record_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    detail_data = response.json()
    assert detail_data["notification"]["title"] == "欢迎使用系统"
    assert detail_data["is_read"] is False

    # 步骤 4: 标记为已读
    response = client.post(
        f"/api/v1/notifications/{record_id}/read",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # 步骤 5: 验证未读数量减少
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    count_data = response.json()
    assert count_data["unread_count"] == 0

    # 验证站内信已标记为已读
    response = client.get(f"/api/v1/notifications/{record_id}", headers=auth_headers)
    assert response.status_code == 200
    detail_data = response.json()
    assert detail_data["is_read"] is True
    assert detail_data["read_at"] is not None


def test_user_view_notifications_with_pagination(client, auth_headers, db_session, test_user):
    """
    场景：用户使用分页查看站内信
    ============================
    1. 创建 25 条站内信
    2. 使用分页查看（每页 10 条）
    3. 验证分页数据正确
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin2",
        email="admin2@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 25 条站内信
    for i in range(25):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"通知 {i+1}",
            content=f"这是第 {i+1} 条通知",
            priority=0,
            created_by=admin.id,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        # 创建记录
        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=False,
        )
        db_session.add(record)
        db_session.commit()

    # 第一页（默认每页 20 条）
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"page": 1, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 25
    assert len(data["items"]) == 10

    # 第二页
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"page": 2, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 25
    assert len(data["items"]) == 10

    # 第三页（剩余 5 条）
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"page": 3, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 25
    assert len(data["items"]) == 5


def test_user_view_empty_notification_list(client, auth_headers):
    """
    场景：用户查看空的站内信列表
    ============================
    1. 新用户没有任何站内信
    2. 查看站内信列表
    3. 验证返回空列表
    """
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["unread_count"] == 0
    assert len(data["items"]) == 0


def test_user_mark_nonexistent_notification_as_read(client, auth_headers):
    """
    场景：用户尝试标记不存在的站内信为已读
    ================================
    1. 使用不存在的 record_id
    2. 尝试标记为已读
    3. 验证返回 404 错误
    """
    fake_record_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/v1/notifications/{fake_record_id}/read",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_user_get_nonexistent_notification_detail(client, auth_headers):
    """
    场景：用户尝试查看不存在的站内信详情
    ================================
    1. 使用不存在的 record_id
    2. 尝试查看详情
    3. 验证返回 404 错误
    """
    fake_record_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(
        f"/api/v1/notifications/{fake_record_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_user_access_notifications_without_auth(client):
    """
    场景：未登录用户尝试访问站内信接口
    ================================
    1. 不提供 token
    2. 尝试访问站内信列表
    3. 验证返回 403 错误
    """
    response = client.get("/api/v1/notifications")
    assert response.status_code == 401

    response = client.get("/api/v1/notifications/unread-count")
    assert response.status_code == 401


def test_user_notifications_ordered_by_created_at(client, auth_headers, db_session, test_user):
    """
    场景：验证站内信按创建时间倒序排列
    ================================
    1. 创建多条站内信（有延迟）
    2. 验证返回列表按创建时间倒序
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash
    import time

    # 创建管理员
    admin = User(
        username="admin3",
        email="admin3@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 3 条站内信，每条间隔一点点时间
    notification_ids = []
    for i in range(3):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"通知 {i+1}",
            content=f"这是第 {i+1} 条通知",
            priority=0,
            created_by=admin.id,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        notification_ids.append(notification.id)

        # 创建记录
        record = NotificationRecord(
            notification_id=notification.id,
            user_id=test_user.id,
            is_read=False,
        )
        db_session.add(record)
        db_session.commit()

        time.sleep(0.01)  # 确保创建时间不同

    # 获取站内信列表
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3

    # 验证顺序：最后创建的应该在最前面
    items = data["items"]
    assert items[0]["notification"]["title"] == "通知 3"
    assert items[1]["notification"]["title"] == "通知 2"
    assert items[2]["notification"]["title"] == "通知 1"
