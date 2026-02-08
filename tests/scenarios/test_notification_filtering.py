"""
站内信筛选功能场景测试

这个场景模拟了用户使用各种筛选条件查询站内信的完整流程。
"""

import pytest


def test_filter_by_read_status(client, auth_headers, db_session, test_user):
    """
    场景：按已读/未读状态筛选站内信
    =============================
    1. 用户有 2 条已读，3 条未读站内信
    2. 筛选只看未读
    3. 筛选只看已读
    4. 验证筛选结果正确
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash
    from datetime import datetime

    # 创建管理员
    admin = User(
        username="admin13",
        email="admin13@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 2 条已读站内信
    for i in range(2):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"已读通知 {i+1}",
            content=f"已读内容 {i+1}",
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

    # 创建 3 条未读站内信
    for i in range(3):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"未读通知 {i+1}",
            content=f"未读内容 {i+1}",
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

    # 测试：筛选未读站内信
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"is_read": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert all(not item["is_read"] for item in data["items"])

    # 测试：筛选已读站内信
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"is_read": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["is_read"] for item in data["items"])

    # 测试：不筛选（获取所有）
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5


def test_filter_by_notification_type(client, auth_headers, db_session, test_user):
    """
    场景：按站内信类型筛选
    =====================
    1. 用户有多种类型的站内信
    2. 筛选 system 类型
    3. 筛选 business 类型
    4. 筛选 announcement 类型
    5. 验证筛选结果正确
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin14",
        email="admin14@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建不同类型的站内信
    notification_types = [
        (NotificationType.SYSTEM, "系统通知"),
        (NotificationType.SYSTEM, "系统升级"),
        (NotificationType.BUSINESS, "订单确认"),
        (NotificationType.BUSINESS, "支付成功"),
        (NotificationType.ANNOUNCEMENT, "放假通知"),
    ]

    for notif_type, title in notification_types:
        notification = Notification(
            type=notif_type,
            title=title,
            content=f"{title}的内容",
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

    # 筛选 system 类型
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"notification_type": "system"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["notification"]["type"] == "system" for item in data["items"])

    # 筛选 business 类型
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"notification_type": "business"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["notification"]["type"] == "business" for item in data["items"])

    # 筛选 announcement 类型
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"notification_type": "announcement"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["notification"]["type"] == "announcement"


def test_filter_by_read_status_and_type_combined(client, auth_headers, db_session, test_user):
    """
    场景：组合筛选条件（已读状态 + 类型）
    ================================
    1. 用户有不同类型和状态的站内信
    2. 筛选 system + 未读
    3. 筛选 business + 已读
    4. 验证组合筛选结果正确
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash
    from datetime import datetime

    # 创建管理员
    admin = User(
        username="admin15",
        email="admin15@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 system 未读
    notification = Notification(
        type=NotificationType.SYSTEM,
        title="系统通知1",
        content="内容",
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

    # 创建 system 已读
    notification = Notification(
        type=NotificationType.SYSTEM,
        title="系统通知2",
        content="内容",
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

    # 创建 business 已读
    notification = Notification(
        type=NotificationType.BUSINESS,
        title="业务通知1",
        content="内容",
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

    # 筛选 system + 未读
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"notification_type": "system", "is_read": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["notification"]["type"] == "system"
    assert data["items"][0]["is_read"] is False

    # 筛选 business + 已读
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"notification_type": "business", "is_read": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["notification"]["type"] == "business"
    assert data["items"][0]["is_read"] is True


def test_filter_with_pagination(client, auth_headers, db_session, test_user):
    """
    场景：筛选 + 分页
    ===============
    1. 用户有 15 条未读站内信
    2. 筛选未读，每页显示 5 条
    3. 验证分页数据正确
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建管理员
    admin = User(
        username="admin16",
        email="admin16@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 15 条未读站内信
    for i in range(15):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"未读通知 {i+1}",
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

    # 筛选未读，第一页（5 条）
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"is_read": False, "page": 1, "page_size": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == 5
    assert data["unread_count"] == 15

    # 筛选未读，第二页（5 条）
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"is_read": False, "page": 2, "page_size": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == 5

    # 筛选未读，第三页（5 条）
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"is_read": False, "page": 3, "page_size": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == 5


def test_filter_empty_results(client, auth_headers):
    """
    场景：筛选条件没有匹配结果
    =======================
    1. 用户没有任何站内信
    2. 筛选 system 类型
    3. 筛选未读状态
    4. 验证返回空列表
    """
    # 筛选 system 类型
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"notification_type": "system"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0

    # 筛选未读
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"is_read": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_filter_with_invalid_page_size(client, auth_headers):
    """
    场景：使用无效的分页参数
    =====================
    1. page_size 超过最大值（100）
    2. page_size 为负数
    3. 验证返回 422 错误
    """
    # page_size 超过最大值
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"page_size": 101},
    )
    assert response.status_code == 422

    # page_size 为负数
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"page_size": -1},
    )
    assert response.status_code == 422

    # page 为 0
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"page": 0},
    )
    assert response.status_code == 422


def test_unread_count_with_filters(client, auth_headers, db_session, test_user):
    """
    场景：验证未读数量不受筛选影响
    =========================
    1. 用户有 5 条未读，5 条已读
    2. 筛选已读站内信
    3. 验证 unread_count 仍然是 5
    """
    from app.models.notification import Notification, NotificationType
    from app.models.notification import NotificationRecord
    from app.models.user import User
    from app.core.security import get_password_hash
    from datetime import datetime

    # 创建管理员
    admin = User(
        username="admin17",
        email="admin17@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(admin)
    db_session.commit()

    # 创建 5 条已读
    for i in range(5):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"已读 {i+1}",
            content="内容",
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

    # 创建 5 条未读
    for i in range(5):
        notification = Notification(
            type=NotificationType.SYSTEM,
            title=f"未读 {i+1}",
            content="内容",
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

    # 筛选已读站内信
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={"is_read": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5  # 返回 5 条已读
    assert data["unread_count"] == 5  # 但未读数量仍然是 5
