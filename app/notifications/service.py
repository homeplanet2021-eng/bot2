from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.time import utcnow
from app.db.models import Subscription
from app.db.repos.notifications import add_notification, has_notification


async def schedule_notifications(session: AsyncSession, subscription: Subscription) -> list[str]:
    notifications = []
    now = utcnow()
    days_left = (subscription.expires_at - now).days
    if days_left <= 3:
        if not await has_notification(session, subscription.user_id, subscription.id, "expires_3d"):
            await add_notification(session, subscription.user_id, subscription.id, "expires_3d")
            notifications.append("expires_3d")
    if days_left <= 1:
        if not await has_notification(session, subscription.user_id, subscription.id, "expires_1d"):
            await add_notification(session, subscription.user_id, subscription.id, "expires_1d")
            notifications.append("expires_1d")
    if subscription.expires_at <= now:
        if not await has_notification(session, subscription.user_id, subscription.id, "expired"):
            await add_notification(session, subscription.user_id, subscription.id, "expired")
            notifications.append("expired")
    return notifications
