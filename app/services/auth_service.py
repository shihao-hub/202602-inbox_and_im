from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token


class AuthService:
    """认证服务"""

    @staticmethod
    def register(db: Session, user_create: UserCreate) -> UserResponse:
        """
        用户注册

        Args:
            db: 数据库会话
            user_create: 用户注册信息

        Returns:
            UserResponse: 用户信息

        Raises:
            HTTPException: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == user_create.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )

        # 检查邮箱是否已存在
        existing_email = db.query(User).filter(User.email == user_create.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用",
            )

        # 创建新用户
        user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=get_password_hash(user_create.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """
        用户认证

        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码

        Returns:
            Optional[User]: 认证成功返回用户，失败返回 None
        """
        # 支持用户名或邮箱登录
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    def login(db: Session, username: str, password: str) -> dict:
        """
        用户登录

        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码

        Returns:
            dict: 包含 access_token 和 refresh_token 的字典

        Raises:
            HTTPException: 用户名或密码错误
        """
        user = AuthService.authenticate(db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()

        # 生成 token
        access_token = create_access_token(data={"user_id": str(user.id), "username": user.username})
        refresh_token = create_refresh_token(data={"user_id": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def refresh(db: Session, user_id: str) -> dict:
        """
        刷新 Token

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            dict: 包含新的 access_token 和 refresh_token 的字典

        Raises:
            HTTPException: 用户不存在
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )

        # 生成新的 token
        access_token = create_access_token(data={"user_id": str(user.id), "username": user.username})
        refresh_token = create_refresh_token(data={"user_id": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
