import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.config import settings

# 使用测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # 或使用 PostgreSQL 测试数据库

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """创建测试客户端"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """获取认证头"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "testuser", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    """创建管理员用户（目前所有用户都有管理员权限）"""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """获取管理员认证头"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def multiple_users(db_session):
    """创建多个测试用户"""
    from app.models.user import User
    from app.core.security import get_password_hash

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

    return users


@pytest.fixture
def user_auth_headers(client, multiple_users):
    """获取多个用户的认证头"""
    headers_list = []
    for i in range(len(multiple_users)):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": f"user{i}", "password": "password123"}
        )
        token = response.json()["access_token"]
        headers_list.append({"Authorization": f"Bearer {token}"})
    return headers_list
