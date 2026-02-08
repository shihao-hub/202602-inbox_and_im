from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_serializer
from app.models.user import UserStatus


class UserCreate(BaseModel):
    """用户注册请求"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """用户登录请求"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应"""

    id: UUID
    username: str
    email: str
    avatar_url: Optional[str] = None
    status: UserStatus
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        """将 UUID 序列化为字符串"""
        return str(value)

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """Token 负载"""

    user_id: str
    username: str
    type: str  # access 或 refresh


class Token(BaseModel):
    """Token 响应"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
