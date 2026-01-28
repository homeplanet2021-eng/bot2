from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PromoCode, PromoRedemption


async def get_promo(session: AsyncSession, code: str) -> PromoCode | None:
    result = await session.execute(select(PromoCode).where(PromoCode.code == code, PromoCode.is_active.is_(True)))
    return result.scalar_one_or_none()


async def count_redemptions(session: AsyncSession, promo_id: int) -> int:
    result = await session.execute(select(func.count(PromoRedemption.id)).where(PromoRedemption.promo_code_id == promo_id))
    return int(result.scalar_one())


async def create_redemption(session: AsyncSession, promo_id: int, user_id: int) -> PromoRedemption:
    redemption = PromoRedemption(promo_code_id=promo_id, user_id=user_id)
    session.add(redemption)
    await session.commit()
    await session.refresh(redemption)
    return redemption


async def has_redemption(session: AsyncSession, promo_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(PromoRedemption).where(PromoRedemption.promo_code_id == promo_id, PromoRedemption.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None
