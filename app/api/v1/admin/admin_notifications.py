from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationSendRequest,
)
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_create: NotificationCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    创建站内信（管理端）

    - **type**: 站内信类型（system, business, reminder, announcement）
    - **title**: 标题
    - **content**: 内容
    - **action_url**: 点击跳转链接（可选）
    - **priority**: 优先级（0:普通 1:重要 2:紧急）
    - **expires_at**: 过期时间（可选）

    注意：此接口仅创建站内信内容，不会发送给用户，需要调用发送接口
    """
    return NotificationService.create_notification(
        db,
        notification_create,
        created_by_id=str(current_user.id),
    )


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    获取站内信列表（管理端）

    返回所有创建的站内信内容（不含用户记录）

    - **skip**: 跳过数量
    - **limit**: 返回数量
    """
    from app.models.notification import Notification

    query = db.query(Notification).order_by(Notification.created_at.desc())
    total = query.count()
    notifications = query.offset(skip).limit(limit).all()

    items = [NotificationResponse.model_validate(notif) for notif in notifications]

    return NotificationListResponse(total=total, items=items)


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    获取站内信详情（管理端）

    - **notification_id**: 站内信 ID
    """
    return NotificationService.get_notification(db, notification_id)


@router.put("/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    更新站内信（管理端）

    - **notification_id**: 站内信 ID
    - **type**: 站内信类型（可选）
    - **title**: 标题（可选）
    - **content**: 内容（可选）
    - **action_url**: 点击跳转链接（可选）
    - **priority**: 优先级（可选）
    - **expires_at**: 过期时间（可选）

    注意：仅更新站内信内容，不影响已发送的用户记录
    """
    return NotificationService.update_notification(db, notification_id, notification_update)


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    删除站内信（管理端）

    - **notification_id**: 站内信 ID

    注意：删除站内信会同时删除所有用户的站内信记录
    """
    NotificationService.delete_notification(db, notification_id)
    return None


@router.post("/notifications/{notification_id}/send")
async def send_notification(
    notification_id: str,
    send_request: NotificationSendRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    发送站内信给用户（管理端）

    - **notification_id**: 站内信 ID
    - **user_ids**: 用户 ID 列表（send_to_all=False 时必填）
    - **send_to_all**: 是否发送给所有用户（如果为 True，则忽略 user_ids）

    返回成功发送的用户数量
    """
    # 验证：如果不是发送给所有人，则必须提供 user_ids
    if not send_request.send_to_all and not send_request.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="send_to_all=False 时，user_ids 不能为空",
        )

    if send_request.send_to_all:
        count = NotificationService.send_to_all_users(db, notification_id)
    else:
        count = NotificationService.send_to_users(db, notification_id, send_request.user_ids)

    return {"message": f"成功发送给 {count} 个用户"}
