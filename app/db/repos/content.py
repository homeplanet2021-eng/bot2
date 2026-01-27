from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ContentPage


async def get_page(session: AsyncSession, key: str) -> ContentPage | None:
    result = await session.execute(select(ContentPage).where(ContentPage.key == key))
    return result.scalar_one_or_none()
