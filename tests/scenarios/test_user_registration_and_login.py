"""
用户注册登录场景测试

这个场景模拟了一个新用户从注册到登录获取 token 的完整流程。
"""

import pytest


def test_new_user_complete_registration_flow(client):
    """
    场景：新用户完整注册流程
    ==========================
    1. 新用户注册账号
    2. 验证用户信息正确
    3. 使用用户名登录
    4. 获取 access_token 和 refresh_token
    5. 使用 token 获取当前用户信息
    6. 验证 token 有效
    """
    # 步骤 1: 新用户注册
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "alicepass123",
        },
    )
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["username"] == "alice"
    assert user_data["email"] == "alice@example.com"
    assert "id" in user_data

    user_id = user_data["id"]

    # 步骤 2: 使用用户名登录
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "alicepass123"},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # 步骤 3: 使用 access_token 获取当前用户信息
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["id"] == user_id
    assert me_data["username"] == "alice"
    assert me_data["email"] == "alice@example.com"


def test_login_with_email_instead_of_username(client, db_session):
    """
    场景：使用邮箱登录
    ===================
    1. 创建用户
    2. 使用邮箱而不是用户名登录
    3. 验证登录成功
    """
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建测试用户
    user = User(
        username="bob",
        email="bob@example.com",
        password_hash=get_password_hash("bobpass123"),
    )
    db_session.add(user)
    db_session.commit()

    # 使用邮箱登录
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "bob@example.com", "password": "bobpass123"},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data


def test_login_failure_scenarios(client, db_session):
    """
    场景：登录失败的各种情况
    =======================
    1. 用户不存在
    2. 密码错误
    3. 验证返回 401 错误
    """
    from app.models.user import User
    from app.core.security import get_password_hash

    # 创建测试用户
    user = User(
        username="charlie",
        email="charlie@example.com",
        password_hash=get_password_hash("charliepass123"),
    )
    db_session.add(user)
    db_session.commit()

    # 测试：用户不存在
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "testpass"},
    )
    assert response.status_code == 401

    # 测试：密码错误
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "charlie", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_user_logout_scenario(client, auth_headers):
    """
    场景：用户登出流程
    ==================
    1. 用户已登录（通过 fixture）
    2. 调用登出接口
    3. 验证返回登出成功消息
    4. 验证 token 仍然可以访问（因为是无状态 JWT）
    """
    # 用户登出
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "登出成功，请删除客户端 Token"

    # 注意：由于是无状态 JWT，token 在过期前仍然有效
    # 客户端需要自行删除 token 来实现登出
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200  # token 仍然有效


def test_duplicate_registration_scenarios(client):
    """
    场景：重复注册的各种情况
    =======================
    1. 注册一个用户
    2. 尝试使用相同用户名注册
    3. 尝试使用相同邮箱注册
    4. 验证返回 400 错误
    """
    # 第一次注册
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "david",
            "email": "david@example.com",
            "password": "davidpass123",
        },
    )
    assert response.status_code == 201

    # 尝试使用相同用户名注册
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "david",
            "email": "david2@example.com",
            "password": "davidpass123",
        },
    )
    assert response.status_code == 400

    # 尝试使用相同邮箱注册
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "david2",
            "email": "david@example.com",
            "password": "davidpass123",
        },
    )
    assert response.status_code == 400


def test_protected_endpoint_without_token(client):
    """
    场景：未提供 token 访问受保护接口
    ================================
    1. 尝试不提供 token 访问 /api/v1/auth/me
    2. 验证返回 403 错误
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_invalid_token_scenario(client):
    """
    场景：使用无效 token 访问受保护接口
    ================================
    1. 使用伪造的 token
    2. 验证返回 403 错误
    """
    headers = {"Authorization": "Bearer invalid_token_12345"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
