from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Payment, PaymentIntent


async def get_intent(session: AsyncSession, intent_id: uuid.UUID) -> PaymentIntent | None:
    result = await session.execute(select(PaymentIntent).where(PaymentIntent.id == intent_id))
    return result.scalar_one_or_none()


async def get_intent_by_id(session: AsyncSession, intent_id: uuid.UUID) -> PaymentIntent | None:
    return await get_intent(session, intent_id)


async def create_intent(session: AsyncSession, intent: PaymentIntent) -> PaymentIntent:
    session.add(intent)
    await session.commit()
    await session.refresh(intent)
    return intent


async def update_intent_status(session: AsyncSession, intent: PaymentIntent, status: str) -> PaymentIntent:
    intent.status = status
    session.add(intent)
    await session.commit()
    await session.refresh(intent)
    return intent


async def create_payment(session: AsyncSession, payment: Payment) -> Payment:
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_payment_by_provider_id(session: AsyncSession, provider_payment_id: str) -> Payment | None:
    result = await session.execute(select(Payment).where(Payment.provider_payment_id == provider_payment_id))
    return result.scalar_one_or_none()
