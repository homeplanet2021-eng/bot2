from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crypto import make_ref_code
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
