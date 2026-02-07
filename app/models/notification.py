from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """站内信类型枚举"""
    SYSTEM = "system"  # 系统通知
    BUSINESS = "business"  # 业务通知
    REMINDER = "reminder"  # 提醒通知
    ANNOUNCEMENT = "announcement"  # 公告


class NotificationPriority(str, enum.Enum):
    """站内信优先级枚举"""
    NORMAL = 0  # 普通
    IMPORTANT = 1  # 重要
    URGENT = 2  # 紧急


class Notification(Base):
    """站内信内容表"""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(String(50), nullable=False, index=True, comment="站内信类型")
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    action_url = Column(String(500), nullable=True, comment="点击跳转链接")
    priority = Column(Integer, default=0, nullable=False, comment="优先级 0:普通 1:重要 2:紧急")
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建者 ID",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")

    # 关系
    created_by_user = relationship(
        "User",
        back_populates="created_notifications",
        foreign_keys=[created_by],
    )
    records = relationship(
        "NotificationRecord",
        back_populates="notification",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, title={self.title})>"


class NotificationRecord(Base):
    """站内信用户记录表"""

    __tablename__ = "notification_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    notification_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="站内信 ID",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户 ID",
    )
    is_read = Column(Boolean, default=False, nullable=False, comment="是否已读")
    read_at = Column(DateTime(timezone=True), nullable=True, comment="阅读时间")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已删除")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    # 关系
    notification = relationship("Notification", back_populates="records")
    user = relationship("User", back_populates="notification_records")

    # 唯一约束：一个用户只能收到一次同一条站内信
    __table_args__ = (UniqueConstraint("notification_id", "user_id", name="unique_notification_user"),)

    def __repr__(self):
        return f"<NotificationRecord(id={self.id}, notification_id={self.notification_id}, user_id={self.user_id}, is_read={self.is_read})>"
