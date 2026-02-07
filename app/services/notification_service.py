from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.notification import Notification, NotificationRecord
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationRecordResponse,
    NotificationRecordListResponse,
)


class NotificationService:
    """站内信服务"""

    @staticmethod
    def create_notification(
        db: Session,
        notification_create: NotificationCreate,
        created_by_id: str,
    ) -> NotificationResponse:
        """
        创建站内信（仅创建内容，不发送给用户）

        Args:
            db: 数据库会话
            notification_create: 站内信创建信息
            created_by_id: 创建者 ID

        Returns:
            NotificationResponse: 站内信信息
        """
        notification = Notification(
            type=notification_create.type,
            title=notification_create.title,
            content=notification_create.content,
            action_url=notification_create.action_url,
            priority=notification_create.priority,
            created_by=created_by_id,
            expires_at=notification_create.expires_at,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        return NotificationResponse.model_validate(notification)

    @staticmethod
    def get_notification(db: Session, notification_id: str) -> NotificationResponse:
        """
        获取站内信详情

        Args:
            db: 数据库会话
            notification_id: 站内信 ID

        Returns:
            NotificationResponse: 站内信信息

        Raises:
            HTTPException: 站内信不存在
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站内信不存在",
            )

        return NotificationResponse.model_validate(notification)

    @staticmethod
    def update_notification(
        db: Session,
        notification_id: str,
        notification_update: NotificationUpdate,
    ) -> NotificationResponse:
        """
        更新站内信

        Args:
            db: 数据库会话
            notification_id: 站内信 ID
            notification_update: 更新信息

        Returns:
            NotificationResponse: 更新后的站内信信息

        Raises:
            HTTPException: 站内信不存在
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站内信不存在",
            )

        # 更新字段
        update_data = notification_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(notification, field, value)

        db.commit()
        db.refresh(notification)

        return NotificationResponse.model_validate(notification)

    @staticmethod
    def delete_notification(db: Session, notification_id: str) -> None:
        """
        删除站内信（会同时删除所有用户的站内信记录）

        Args:
            db: 数据库会话
            notification_id: 站内信 ID

        Raises:
            HTTPException: 站内信不存在
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站内信不存在",
            )

        db.delete(notification)
        db.commit()

    @staticmethod
    def send_to_users(
        db: Session,
        notification_id: str,
        user_ids: List[str],
    ) -> int:
        """
        发送站内信给指定用户

        Args:
            db: 数据库会话
            notification_id: 站内信 ID
            user_ids: 用户 ID 列表

        Returns:
            int: 成功发送的用户数量

        Raises:
            HTTPException: 站内信不存在
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站内信不存在",
            )

        # 批量创建站内信记录
        records = []
        for user_id in user_ids:
            # 检查是否已存在
            existing = (
                db.query(NotificationRecord)
                .filter(
                    NotificationRecord.notification_id == notification_id,
                    NotificationRecord.user_id == user_id,
                )
                .first()
            )
            if not existing:
                records.append(
                    NotificationRecord(
                        notification_id=notification_id,
                        user_id=user_id,
                    )
                )

        db.bulk_save_objects(records)
        db.commit()

        return len(records)

    @staticmethod
    def send_to_all_users(
        db: Session,
        notification_id: str,
    ) -> int:
        """
        发送站内信给所有用户

        Args:
            db: 数据库会话
            notification_id: 站内信 ID

        Returns:
            int: 成功发送的用户数量

        Raises:
            HTTPException: 站内信不存在
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站内信不存在",
            )

        # 获取所有用户 ID
        all_users = db.query(User.id).all()
        user_ids = [str(user.id) for user in all_users]

        return NotificationService.send_to_users(db, notification_id, user_ids)

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: str,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> NotificationRecordListResponse:
        """
        获取用户的站内信列表

        Args:
            db: 数据库会话
            user_id: 用户 ID
            is_read: 筛选已读/未读（None 表示全部）
            notification_type: 站内信类型筛选
            skip: 跳过数量（分页）
            limit: 返回数量（分页）

        Returns:
            NotificationRecordListResponse: 站内信列表
        """
        # 构建查询
        query = (
            db.query(NotificationRecord)
            .filter(NotificationRecord.user_id == user_id, NotificationRecord.is_deleted == False)
            .join(Notification)
        )

        # 筛选条件
        if is_read is not None:
            query = query.filter(NotificationRecord.is_read == is_read)

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        # 排序（最新站内信在前）
        query = query.order_by(NotificationRecord.created_at.desc())

        # 总数
        total = query.count()

        # 未读数量
        unread_count = (
            db.query(NotificationRecord)
            .filter(
                NotificationRecord.user_id == user_id,
                NotificationRecord.is_read == False,
                NotificationRecord.is_deleted == False,
            )
            .count()
        )

        # 分页
        records = query.offset(skip).limit(limit).all()

        # 转换为响应格式
        items = [NotificationRecordResponse.model_validate(record) for record in records]

        return NotificationRecordListResponse(
            total=total,
            unread_count=unread_count,
            items=items,
        )

    @staticmethod
    def get_notification_detail(
        db: Session,
        user_id: str,
        record_id: str,
    ) -> NotificationRecordResponse:
        """
        获取站内信详情

        Args:
            db: 数据库会话
            user_id: 用户 ID
            record_id: 站内信记录 ID

        Returns:
            NotificationRecordResponse: 站内信详情

        Raises:
            HTTPException: 站内信不存在
        """
        record = (
            db.query(NotificationRecord)
            .filter(
                NotificationRecord.id == record_id,
                NotificationRecord.user_id == user_id,
                NotificationRecord.is_deleted == False,
            )
            .first()
        )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站内信不存在",
            )

        return NotificationRecordResponse.model_validate(record)

    @staticmethod
    def mark_as_read(
        db: Session,
        user_id: str,
        record_id: str,
    ) -> None:
        """
        标记站内信为已读

        Args:
            db: 数据库会话
            user_id: 用户 ID
            record_id: 站内信记录 ID

        Raises:
            HTTPException: 站内信不存在
        """
        record = (
            db.query(NotificationRecord)
            .filter(
                NotificationRecord.id == record_id,
                NotificationRecord.user_id == user_id,
                NotificationRecord.is_deleted == False,
            )
            .first()
        )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站内信不存在",
            )

        if not record.is_read:
            record.is_read = True
            record.read_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def mark_all_as_read(db: Session, user_id: str) -> int:
        """
        标记所有站内信为已读

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            int: 标记为已读的数量
        """
        # 查询未读的站内信
        unread_records = (
            db.query(NotificationRecord)
            .filter(
                NotificationRecord.user_id == user_id,
                NotificationRecord.is_read == False,
                NotificationRecord.is_deleted == False,
            )
            .all()
        )

        count = 0
        for record in unread_records:
            record.is_read = True
            record.read_at = datetime.utcnow()
            count += 1

        db.commit()
        return count

    @staticmethod
    def delete_notification_record(
        db: Session,
        user_id: str,
        record_id: str,
    ) -> None:
        """
        删除站内信（软删除）

        Args:
            db: 数据库会话
            user_id: 用户 ID
            record_id: 站内信记录 ID

        Raises:
            HTTPException: 站内信不存在
        """
        record = (
            db.query(NotificationRecord)
            .filter(
                NotificationRecord.id == record_id,
                NotificationRecord.user_id == user_id,
            )
            .first()
        )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站内信不存在",
            )

        record.is_deleted = True
        record.deleted_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def get_unread_count(db: Session, user_id: str) -> int:
        """
        获取未读站内信数量

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            int: 未读数量
        """
        return (
            db.query(NotificationRecord)
            .filter(
                NotificationRecord.user_id == user_id,
                NotificationRecord.is_read == False,
                NotificationRecord.is_deleted == False,
            )
            .count()
        )
