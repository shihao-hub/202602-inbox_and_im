from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationRecordResponse, NotificationRecordListResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=NotificationRecordListResponse)
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="筛选已读/未读"),
    notification_type: Optional[str] = Query(None, description="站内信类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的站内信列表

    支持以下筛选：
    - **is_read**: 筛选已读/未读站内信
    - **notification_type**: 站内信类型筛选（system, business, reminder, announcement）
    - **page**: 页码（从 1 开始）
    - **page_size**: 每页数量（1-100）
    """
    skip = (page - 1) * page_size
    return NotificationService.get_user_notifications(
        db,
        user_id=str(current_user.id),
        is_read=is_read,
        notification_type=notification_type,
        skip=skip,
        limit=page_size,
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取未读站内信数量

    返回当前用户的未读站内信数量
    """
    count = NotificationService.get_unread_count(db, str(current_user.id))
    return {"unread_count": count}


@router.get("/{record_id}", response_model=NotificationRecordResponse)
async def get_notification_detail(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取站内信详情

    - **record_id**: 站内信记录 ID
    """
    return NotificationService.get_notification_detail(db, str(current_user.id), record_id)


@router.post("/{record_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    标记站内信为已读

    - **record_id**: 站内信记录 ID
    """
    NotificationService.mark_as_read(db, str(current_user.id), record_id)
    return None


@router.post("/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    全部标记已读

    将当前用户的所有未读站内信标记为已读
    """
    count = NotificationService.mark_all_as_read(db, str(current_user.id))
    return {"message": f"已将 {count} 条站内信标记为已读"}


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    删除站内信

    - **record_id**: 站内信记录 ID

    注意：这是软删除，站内信会被标记为已删除但不会从数据库中物理删除
    """
    NotificationService.delete_notification_record(db, str(current_user.id), record_id)
    return None
