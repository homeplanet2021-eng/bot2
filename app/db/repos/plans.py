from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan


async def list_active_plans(session: AsyncSession) -> list[Plan]:
    result = await session.execute(select(Plan).where(Plan.is_active.is_(True)))
    return list(result.scalars().all())


async def get_plan(session: AsyncSession, plan_code: str) -> Plan | None:
    result = await session.execute(select(Plan).where(Plan.plan_code == plan_code))
    return result.scalar_one_or_none()
