from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationLog


async def add_notification(session: AsyncSession, user_id: int, subscription_id: int, type_: str) -> NotificationLog:
    log = NotificationLog(user_id=user_id, subscription_id=subscription_id, type=type_)
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def has_notification(session: AsyncSession, user_id: int, subscription_id: int, type_: str) -> bool:
    result = await session.execute(
        select(NotificationLog).where(
            NotificationLog.user_id == user_id,
            NotificationLog.subscription_id == subscription_id,
            NotificationLog.type == type_,
        )
    )
    return result.scalar_one_or_none() is not None
