def test_create_notification(client, auth_headers):
    """测试创建站内信"""
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
    data = response.json()
    assert data["type"] == "system"
    assert data["title"] == "测试通知"
    assert "id" in data


def test_send_notification_to_user(client, auth_headers, db_session, test_user):
    """测试发送站内信给用户"""
    # 先创建站内信
    create_response = client.post(
        "/api/v1/admin/notifications",
        headers=auth_headers,
        json={
            "type": "system",
            "title": "测试通知",
            "content": "这是一条测试通知",
            "priority": 0,
        },
    )
    notification_id = create_response.json()["id"]

    # 发送站内信
    send_response = client.post(
        f"/api/v1/admin/notifications/{notification_id}/send",
        headers=auth_headers,
        json={"user_ids": [str(test_user.id)], "send_to_all": False},
    )
    assert send_response.status_code == 200


def test_get_user_notifications(client, auth_headers, db_session, test_user):
    """测试获取用户站内信列表"""
    response = client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "unread_count" in data
    assert "items" in data


def test_mark_notification_as_read(client, auth_headers, db_session, test_user):
    """测试标记站内信为已读"""
    # 先获取站内信列表
    list_response = client.get("/api/v1/notifications", headers=auth_headers)
    notifications = list_response.json()["items"]

    if notifications:
        record_id = notifications[0]["id"]
        response = client.post(f"/api/v1/notifications/{record_id}/read", headers=auth_headers)
        assert response.status_code == 204


def test_get_unread_count(client, auth_headers):
    """测试获取未读数量"""
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "unread_count" in data
