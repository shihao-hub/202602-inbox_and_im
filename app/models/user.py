from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    avatar_url = Column(String(500), nullable=True, comment="头像 URL")
    status = Column(
        SQLEnum(UserStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=UserStatus.OFFLINE,
        nullable=False,
        comment="用户状态",
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )

    # 关系
    created_notifications = relationship(
        "Notification",
        back_populates="created_by_user",
        foreign_keys="Notification.created_by",
    )
    notification_records = relationship(
        "NotificationRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
