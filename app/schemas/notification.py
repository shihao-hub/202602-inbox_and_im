from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer
from app.models.notification import NotificationType


class NotificationCreate(BaseModel):
    """创建站内信请求"""

    type: NotificationType = Field(..., description="站内信类型")
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=1, description="内容")
    action_url: Optional[str] = Field(None, max_length=500, description="点击跳转链接")
    priority: int = Field(default=0, ge=0, le=2, description="优先级 0:普通 1:重要 2:紧急")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class NotificationUpdate(BaseModel):
    """更新站内信请求"""

    type: Optional[NotificationType] = Field(None, description="站内信类型")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="标题")
    content: Optional[str] = Field(None, min_length=1, description="内容")
    action_url: Optional[str] = Field(None, max_length=500, description="点击跳转链接")
    priority: Optional[int] = Field(None, ge=0, le=2, description="优先级")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class NotificationSendRequest(BaseModel):
    """发送站内信请求"""

    user_ids: List[str] = Field(default_factory=list, description="用户 ID 列表（send_to_all=False 时必填）")
    send_to_all: bool = Field(default=False, description="是否发送给所有用户")


class NotificationResponse(BaseModel):
    """站内信响应"""

    id: UUID
    type: str
    title: str
    content: str
    action_url: Optional[str] = None
    priority: int
    created_by: Optional[UUID] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    @field_serializer('id', 'created_by')
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        """将 UUID 序列化为字符串"""
        return str(value) if value else None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """站内信列表响应（管理端）"""

    total: int
    items: List[NotificationResponse]


class NotificationRecordResponse(BaseModel):
    """站内信记录响应（用户端）"""

    id: UUID
    notification: NotificationResponse
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    @field_serializer('id')
    def serialize_uuid(self, value: UUID) -> str:
        """将 UUID 序列化为字符串"""
        return str(value)

    class Config:
        from_attributes = True


class NotificationRecordListResponse(BaseModel):
    """站内信记录列表响应（用户端）"""

    total: int
    unread_count: int
    items: List[NotificationRecordResponse]
