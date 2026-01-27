from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Location, PlanLocationMapping


async def list_locations(session: AsyncSession) -> list[Location]:
    result = await session.execute(select(Location).where(Location.is_active.is_(True)))
    return list(result.scalars().all())


async def get_mapping(session: AsyncSession, plan_code: str, location_code: str) -> PlanLocationMapping | None:
    result = await session.execute(
        select(PlanLocationMapping).where(
            PlanLocationMapping.plan_code == plan_code,
            PlanLocationMapping.location_code == location_code,
            PlanLocationMapping.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()
