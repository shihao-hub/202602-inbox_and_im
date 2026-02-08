"""
管理员创建和发送站内信场景测试

这个场景模拟了管理员从创建站内信到发送给用户的完整流程。
"""

from datetime import datetime, timedelta
import pytest


def test_admin_create_and_send_notification_to_single_user(client, auth_headers, db_session, test_user):
    """
    场景：管理员创建站内信并发送给单个用户
    ========================================
    1. 管理员创建一条系统通知
    2. 获取站内信 ID
    3. 将站内信发送给指定用户
    4. 验证发送成功
    5. 用户查看收到的站内信
    """
    # 步骤 1: 管理员创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "系统维护通知",
            "content": "系统将于今晚 22:00 进行维护，预计时长 2 小时。",
            "priority": 1,
            "action_url": "https://example.com/maintenance",
        },
    )
    assert response.status_code == 201
    notification_data = response.json()
    assert notification_data["type"] == "system"
    assert notification_data["title"] == "系统维护通知"
    assert notification_data["priority"] == 1
    assert "id" in notification_data

    notification_id = notification_data["id"]

    # 步骤 2: 管理员发送站内信给指定用户
    response = client.post(
        f"/api/v1/admin/notifications/{notification_id}/send",
        headers=auth_headers,
        json={
            "user_ids": [str(test_user.id)],
            "send_to_all": False,
        },
    )
    assert response.status_code == 200
    send_result = response.json()
    assert "成功发送给 1 个用户" in send_result["message"]

    # 步骤 3: 用户查看收到的站内信
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    notifications = response.json()
    assert notifications["total"] == 1
    assert notifications["unread_count"] == 1
    assert len(notifications["items"]) == 1

    received_notification = notifications["items"][0]
    assert received_notification["notification"]["title"] == "系统维护通知"
    assert received_notification["is_read"] is False


def test_admin_create_different_types_of_notifications(client, auth_headers, db_session, test_user):
    """
    场景：管理员创建不同类型的站内信
    ================================
    1. 创建系统通知 (system)
    2. 创建业务通知 (business)
    3. 创建提醒通知 (reminder)
    4. 创建公告 (announcement)
    5. 验证所有类型创建成功
    """
    notification_types = [
        ("system", "系统升级", "系统已升级到最新版本"),
        ("business", "订单确认", "您的订单已确认"),
        ("reminder", "会议提醒", "您有一个会议将在 30 分钟后开始"),
        ("announcement", "放假通知", "下周一开始放假三天"),
    ]

    notification_ids = []

    for notif_type, title, content in notification_types:
        response = client.post(
            "/api/v1/admin/notifications",
            headers=auth_headers,
            json={
                "type": notif_type,
                "title": title,
                "content": content,
                "priority": 0,
            },
        )
        assert response.status_code == 201
        notification_data = response.json()
        assert notification_data["type"] == notif_type
        notification_ids.append(notification_data["id"])

    # 验证所有站内信都已创建
    assert len(notification_ids) == 4


def test_admin_send_notification_with_expiry(client, auth_headers, db_session, test_user):
    """
    场景：管理员创建带过期时间的站内信
    ================================
    1. 创建带过期时间的站内信
    2. 发送给用户
    3. 验证过期时间设置正确
    """
    expires_at = datetime.now() + timedelta(days=7)

    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "announcement",
            "title": "限时活动",
            "content": "限时优惠活动，7 天后结束",
            "priority": 2,
            "expires_at": expires_at.isoformat(),
        },
    )
    assert response.status_code == 201
    notification_data = response.json()
    assert notification_data["expires_at"] is not None

    notification_id = notification_data["id"]

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


def test_admin_send_notification_to_all_users(client, auth_headers, db_session):
    """
    场景：管理员发送站内信给所有用户
    ================================
    1. 创建多个测试用户
    2. 管理员创建站内信
    3. 发送给所有用户
    4. 验证所有用户都收到站内信
    """
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建 5 个测试用户
    users = []
    for i in range(5):
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password_hash=get_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        users.append(user)

    # 创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "announcement",
            "title": "全员公告",
            "content": "这是一条全员公告",
            "priority": 1,
        },
    )
    assert response.status_code == 201
    notification_id = response.json()["id"]

    # 发送给所有用户
    response = client.post(
        f"/api/v1/admin/notifications/{notification_id}/send",
        headers=auth_headers,
        json={
            "user_ids": [],
            "send_to_all": True,
        },
    )
    assert response.status_code == 200
    send_result = response.json()
    assert "成功发送给 5 个用户" in send_result["message"]


def test_admin_list_and_view_notifications(client, auth_headers):
    """
    场景：管理员查看站内信列表和详情
    ================================
    1. 创建多条站内信
    2. 获取站内信列表
    3. 验证分页功能
    4. 查看站内信详情
    """
    # 创建 3 条站内信
    notification_ids = []
    for i in range(3):
        response = client.post(
            "/api/v1/admin/notifications",
            headers=auth_headers,
            json={
                "type": "system",
                "title": f"通知 {i+1}",
                "content": f"这是第 {i+1} 条通知",
                "priority": 0,
            },
        )
        assert response.status_code == 201
        notification_ids.append(response.json()["id"])

    # 获取站内信列表
    response = client.get("/api/v1/admin/notifications", headers=auth_headers)
    assert response.status_code == 200
    list_data = response.json()
    assert list_data["total"] == 3
    assert len(list_data["items"]) == 3

    # 测试分页
    response = client.get(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        params={"skip": 0, "limit": 2},
    )
    assert response.status_code == 200
    list_data = response.json()
    assert len(list_data["items"]) == 2

    # 查看站内信详情
    response = client.get(
        f"/api/v1/admin/notifications/{notification_ids[0]}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    detail_data = response.json()
    assert detail_data["title"] == "通知 1"


def test_admin_create_notification_with_validation(client, auth_headers):
    """
    场景：管理员创建站内信时的数据验证
    ================================
    1. 测试必填字段缺失
    2. 测试标题长度限制
    3. 测试优先级范围
    4. 验证返回 422 错误
    """
    # 测试：缺少必填字段
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            # 缺少 title
            "content": "测试内容",
        },
    )
    assert response.status_code == 422

    # 测试：标题过长（超过 200 字符）
    long_title = "A" * 201
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": long_title,
            "content": "测试内容",
        },
    )
    assert response.status_code == 422

    # 测试：优先级超出范围
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "测试标题",
            "content": "测试内容",
            "priority": 5,  # 超出范围（0-2）
        },
    )
    assert response.status_code == 422


def test_admin_send_duplicate_notification_to_same_user(client, auth_headers, db_session, test_user):
    """
    场景：重复发送站内信给同一用户
    =============================
    1. 创建站内信
    2. 第一次发送给用户
    3. 第二次尝试发送给同一用户
    4. 验证不会重复创建记录（唯一约束）
    """
    # 创建站内信
    response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "测试通知",
            "content": "这是一条测试通知",
            "priority": 0,
        },
    )
    assert response.status_code == 201
    notification_id = response.json()["id"]

    # 第一次发送
    response = client.post(
        f"/api/v1/admin/notifications/{notification_id}/send",
        headers=auth_headers,
        json={
            "user_ids": [str(test_user.id)],
            "send_to_all": False,
        },
    )
    assert response.status_code == 200
    assert "成功发送给 1 个用户" in response.json()["message"]

    # 第二次发送（应该不会重复创建记录）
    response = client.post(
        f"/api/v1/admin/notifications/{notification_id}/send",
        headers=auth_headers,
        json={
            "user_ids": [str(test_user.id)],
            "send_to_all": False,
        },
    )
    # 服务可能返回成功但实际没有创建新记录
    # 或者返回错误，具体取决于实现
    # 这里我们验证用户只有一条记录
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    notifications = response.json()
    assert notifications["total"] == 1  # 只有一条记录
