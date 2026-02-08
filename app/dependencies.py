from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_access_token
from app.models.user import User

security = HTTPBearer()

# 临时禁用认证的开关
DISABLE_AUTH = True


def _get_or_create_default_user(db: Session) -> User:
    """
    获取或创建默认测试用户

    临时用于测试环境，正式环境应移除
    """
    # 尝试查找默认用户
    default_user = db.query(User).filter(User.username == "test_user").first()
    if default_user:
        return default_user

    # 不存在则创建
    from uuid import uuid4
    default_user = User(
        id=uuid4(),
        username="test_user",
        email="test@example.com",
        password_hash="dummy_hash",  # 临时使用，不验证密码
    )
    db.add(default_user)
    db.commit()
    db.refresh(default_user)
    return default_user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    """
    获取当前用户（可选）

    如果没有 token 或 token 无效，返回 None
    """
    # 临时：禁用认证，返回默认用户
    if DISABLE_AUTH:
        return _get_or_create_default_user(db)

    try:
        token = credentials.credentials
        payload = verify_access_token(token)
        if payload is None:
            return None

        user_id = payload.get("user_id")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前用户（必须）

    验证 JWT token 并返回当前用户

    Raises:
        HTTPException: token 无效或用户不存在
    """
    # 临时：禁用认证，返回默认用户
    if DISABLE_AUTH:
        return _get_or_create_default_user(db)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限

    Raises:
        HTTPException: 用户不是管理员
    """
    # TODO: 实现管理员角色系统
    # 目前暂时允许所有用户访问管理接口
    return current_user
