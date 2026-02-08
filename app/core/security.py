from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 密码是否匹配
    """
    # 将 hashed_password 转换为 bytes
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')

    # 将 plain_password 转换为 bytes
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')

    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    对密码进行哈希

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    # 将密码转换为 bytes
    if isinstance(password, str):
        password = password.encode('utf-8')

    # 生成 salt 并哈希
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password, salt)

    # 返回字符串
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 Access Token

    Args:
        data: 要编码的数据（通常包含 user_id）
        expires_delta: 过期时间增量

    Returns:
        str: JWT Token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建 Refresh Token

    Args:
        data: 要编码的数据（通常包含 user_id）

    Returns:
        str: JWT Refresh Token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    解码 Token

    Args:
        token: JWT Token

    Returns:
        Optional[dict]: 解码后的数据，失败返回 None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[dict]:
    """
    验证 Access Token

    Args:
        token: JWT Token

    Returns:
        Optional[dict]: Token 数据，验证失败返回 None
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "access":
        return None
    return payload


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    验证 Refresh Token

    Args:
        token: JWT Token

    Returns:
        Optional[dict]: Token 数据，验证失败返回 None
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "refresh":
        return None
    return payload
