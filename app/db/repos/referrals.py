from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReferralEarning


async def create_referral(session: AsyncSession, referrer_id: int, referred_id: int, payment_id: uuid.UUID, amount_stars: int) -> ReferralEarning:
    referral = ReferralEarning(
        referrer_id=referrer_id,
        referred_id=referred_id,
        payment_id=payment_id,
        amount_stars=amount_stars,
    )
    session.add(referral)
    await session.commit()
    await session.refresh(referral)
    return referral


async def get_referral_by_payment(session: AsyncSession, payment_id: uuid.UUID) -> ReferralEarning | None:
    result = await session.execute(select(ReferralEarning).where(ReferralEarning.payment_id == payment_id))
    return result.scalar_one_or_none()
