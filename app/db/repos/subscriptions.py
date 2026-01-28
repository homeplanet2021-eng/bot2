from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Subscription


async def list_user_subscriptions(session: AsyncSession, user_id: int) -> list[Subscription]:
    result = await session.execute(select(Subscription).where(Subscription.user_id == user_id))
    return list(result.scalars().all())


async def list_all_subscriptions(session: AsyncSession) -> list[Subscription]:
    result = await session.execute(select(Subscription))
    return list(result.scalars().all())


async def get_subscription(session: AsyncSession, sub_id: int, user_id: int | None) -> Subscription | None:
    query = select(Subscription).where(Subscription.id == sub_id)
    if user_id is not None:
        query = query.where(Subscription.user_id == user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_active_subscription(
    session: AsyncSession,
    user_id: int,
    plan_code: str,
    location_code: str,
) -> Subscription | None:
    result = await session.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.plan_code == plan_code,
            Subscription.location_code == location_code,
            Subscription.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def update_subscription(session: AsyncSession, subscription: Subscription) -> Subscription:
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def create_subscription(
    session: AsyncSession,
    user_id: int,
    plan_code: str,
    location_code: str,
    expires_at: datetime,
    status: str,
    provision_meta: dict,
) -> Subscription:
    sub = Subscription(
        user_id=user_id,
        plan_code=plan_code,
        location_code=location_code,
        expires_at=expires_at,
        status=status,
        provision_meta=provision_meta,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub
