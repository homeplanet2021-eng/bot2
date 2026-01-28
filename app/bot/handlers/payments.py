from __future__ import annotations

import uuid

from aiogram import Bot, F, Router
from aiogram.types import Message, PreCheckoutQuery

from app.bot.ui.keyboards import back_home_keyboard
from app.bot.ui.render import ensure_root
from app.bot.ui.texts import PAYMENT_SUCCESS_TEXT
from app.db.models import JobOutbox
from app.db.repos.jobs import enqueue_job_safe
from app.db.repos.payments import get_intent_by_id
from app.db.session import SessionLocal
from app.payments.providers.stars import StarsProvider
from app.payments.service import PaymentService

router = Router()


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery, bot: Bot) -> None:
    try:
        intent_id = uuid.UUID(query.invoice_payload)
    except ValueError:
        await query.answer(ok=False, error_message="Некорректный платеж.")
        return
    async with SessionLocal() as session:
        intent = await get_intent_by_id(session, intent_id)
        if not intent or intent.status not in {"created", "invoiced"}:
            await query.answer(ok=False, error_message="Платёж недоступен.")
            return
        service = PaymentService(StarsProvider())
        await service.mark_invoiced(session, intent)
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, bot: Bot) -> None:
    payment_data = message.successful_payment
    if not payment_data:
        return
    try:
        intent_id = uuid.UUID(payment_data.invoice_payload)
    except ValueError:
        return
    async with SessionLocal() as session:
        intent = await get_intent_by_id(session, intent_id)
        if not intent:
            return
        service = PaymentService(StarsProvider())
        payment = await service.handle_successful_payment(
            session,
            intent,
            provider_payment_id=payment_data.telegram_payment_charge_id,
            raw=payment_data.model_dump(),
        )
        period_days = intent.period_days + int(intent.meta.get("free_days", 0))
        job = JobOutbox(
            job_type="provision_subscription",
            payload={
                "user_id": intent.user_id,
                "plan_code": intent.plan_code,
                "location_code": intent.location_code,
                "period_days": period_days,
                "payment_id": str(payment.id),
            },
            status="pending",
            idempotency_key=f"payment:{payment.id}",
        )
        await enqueue_job_safe(session, job)
    await ensure_root(bot, message.chat.id, message.from_user.id, PAYMENT_SUCCESS_TEXT, back_home_keyboard())
