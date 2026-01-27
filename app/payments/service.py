from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.time import utcnow
from app.db.models import Payment, PaymentIntent
from app.db.repos.payments import create_intent, create_payment, get_payment_by_provider_id, update_intent_status
from app.db.repos.promo import create_redemption
from app.db.repos.referrals import create_referral, get_referral_by_payment
from app.db.repos.users import get_user
from app.payments.providers.base import PaymentProvider


class PaymentService:
    def __init__(self, provider: PaymentProvider) -> None:
        self.provider = provider

    async def create_intent(
        self,
        session: AsyncSession,
        user_id: int,
        plan_code: str,
        period_days: int,
        location_code: str,
        amount_stars: int,
        promo_code_id: int | None = None,
    ) -> PaymentIntent:
        intent = PaymentIntent(
            user_id=user_id,
            plan_code=plan_code,
            period_days=period_days,
            location_code=location_code,
            amount_stars=amount_stars,
            provider=self.provider.name,
            status="created",
            promo_code_id=promo_code_id,
            created_at=utcnow(),
            expires_at=utcnow() + timedelta(hours=1),
            meta={},
        )
        return await create_intent(session, intent)

    async def mark_invoiced(self, session: AsyncSession, intent: PaymentIntent) -> PaymentIntent:
        return await update_intent_status(session, intent, "invoiced")

    async def handle_successful_payment(
        self,
        session: AsyncSession,
        intent: PaymentIntent,
        provider_payment_id: str,
        raw: dict,
    ) -> Payment:
        existing = await get_payment_by_provider_id(session, provider_payment_id)
        if existing:
            return existing

        payment = Payment(
            intent_id=intent.id,
            user_id=intent.user_id,
            plan_code=intent.plan_code,
            provider=self.provider.name,
            provider_payment_id=provider_payment_id,
            amount_stars=intent.amount_stars,
            currency="XTR",
            status="paid",
            raw=raw,
        )
        payment = await create_payment(session, payment)

        if intent.promo_code_id:
            await create_redemption(session, intent.promo_code_id, intent.user_id)

        user = await get_user(session, intent.user_id)
        if user and user.referrer_id:
            existing_ref = await get_referral_by_payment(session, payment.id)
            if not existing_ref:
                await create_referral(session, user.referrer_id, user.tg_id, payment.id, int(payment.amount_stars * 0.2))

        await update_intent_status(session, intent, "paid")
        return payment
