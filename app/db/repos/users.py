from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crypto import make_ref_code
from app.common.time import utcnow
from app.db.models import User


async def get_user(session: AsyncSession, tg_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_user_by_ref_code(session: AsyncSession, ref_code: str) -> User | None:
    result = await session.execute(select(User).where(User.ref_code == ref_code))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    tg_id: int,
    username: str | None,
    referrer_id: int | None = None,
) -> User:
    user = User(tg_id=tg_id, username=username, referrer_id=referrer_id, ref_code=make_ref_code())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def mark_trial_used(session: AsyncSession, tg_id: int, at_time=None) -> User | None:
    user = await get_user(session, tg_id)
    if not user:
        return None
    user.trial_used_at = at_time or utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def set_adguard(session: AsyncSession, tg_id: int, enabled: bool) -> User | None:
    user = await get_user(session, tg_id)
    if not user:
        return None
    user.adguard_enabled = enabled
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
