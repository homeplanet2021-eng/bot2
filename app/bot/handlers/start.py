from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.ui import callbacks
from app.bot.ui.keyboards import admin_keyboard, back_home_keyboard, buy_keyboard, home_keyboard, support_keyboard
from app.bot.ui.render import ensure_root, sync_root
from app.bot.ui.texts import (
    ADGUARD_TEXT,
    ADMIN_TEXT,
    BUY_TEXT,
    DEVICE_GUIDE_TEXT,
    FAQ_TEXT,
    HOME_TEXT,
    OFFER_TEXT,
    PAYMENT_SUCCESS_TEXT,
    PRIVACY_TEXT,
    PROMO_APPLIED_TEXT,
    PROMO_TEXT,
    REFERRAL_TEXT,
    SUBSCRIPTIONS_TEXT,
    SUPPORT_TEXT,
    TERMS_TEXT,
    TRIAL_USED_TEXT,
)
from app.common.config import settings
from app.common.redis import rate_limit, user_lock
from app.common.time import utcnow
from app.db.models import JobOutbox
from app.db.repos.content import get_page
from app.db.repos.jobs import enqueue_job_safe
from app.db.repos.locations import list_locations
from app.db.repos.plans import get_plan, list_active_plans
from app.db.repos.promo import get_promo, has_redemption, count_redemptions
from app.db.repos.subscriptions import get_subscription, list_user_subscriptions
from app.db.repos.tickets import (
    add_message,
    create_ticket,
    get_ticket,
    list_ticket_messages,
    list_tickets,
    update_ticket_status,
)
from app.db.repos.users import create_user, get_user, get_user_by_ref_code, mark_trial_used, set_adguard
from app.db.session import SessionLocal
from app.payments.providers.stars import StarsProvider
from app.payments.service import PaymentService

router = Router()


class UserFlow(StatesGroup):
    awaiting_promo = State()
    awaiting_support_message = State()
    awaiting_ticket_reply = State()
    awaiting_admin_reply = State()


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    ref_code = None
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) == 2:
            ref_code = parts[1].strip()

    async with user_lock(message.from_user.id) as acquired:
        if not acquired:
            await message.answer("Запрос уже обрабатывается. Попробуйте чуть позже.")
            return
        async with SessionLocal() as session:
            user = await get_user(session, message.from_user.id)
            if not user:
                referrer_id = None
                if ref_code:
                    ref_user = await get_user_by_ref_code(session, ref_code)
                    if ref_user:
                        referrer_id = ref_user.tg_id
                user = await create_user(session, message.from_user.id, message.from_user.username, referrer_id)
    await state.clear()
    await ensure_root(
        bot,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        text=HOME_TEXT,
        reply_markup=home_keyboard(message.from_user.id in settings.admin_ids()),
    )


def _promo_discount(amount: int, promo) -> tuple[int, int]:
    discount = 0
    if promo.discount_percent:
        discount = int(amount * promo.discount_percent / 100)
    if promo.discount_stars:
        discount = max(discount, promo.discount_stars)
    return max(0, discount), promo.free_days or 0


def _format_buy_summary(plan, location, amount, discount, free_days) -> str:
    lines = [BUY_TEXT]
    if plan:
        lines.append(f"\nТариф: {plan.title} ({plan.duration_days} дн.)")
    if location:
        lines.append(f"Локация: {location.title}")
    lines.append(f"Стоимость: {amount} Stars")
    if discount:
        lines.append(f"Скидка: {discount} Stars")
    if free_days:
        lines.append(f"Бонусные дни: {free_days}")
    return "\n".join(lines)


async def _render_content_page(bot: Bot, chat_id: int, user_id: int, key: str, fallback_text: str) -> None:
    async with SessionLocal() as session:
        page = await get_page(session, key)
        text = f"{page.title}\n\n{page.body_md}" if page else fallback_text
    await ensure_root(bot, chat_id, user_id, text, back_home_keyboard())


async def _render_plan_list(bot: Bot, chat_id: int, user_id: int) -> None:
    async with SessionLocal() as session:
        plans = await list_active_plans(session)
    buttons = [
        [InlineKeyboardButton(text=f"{plan.title} • {plan.price_stars}⭐", callback_data=callbacks.pack(callbacks.BUY_PLAN, plan.plan_code))]
        for plan in plans
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)])
    await ensure_root(
        bot,
        chat_id,
        user_id,
        "Выберите тариф:",
        InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query()
async def callback_handler(query: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    await query.answer("Готово")
    if not query.message or not query.from_user:
        return
    sync_root(query.from_user.id, query.message.message_id)
    action, parts = callbacks.parse(query.data)
    user_id = query.from_user.id
    chat_id = query.message.chat.id

    if action == callbacks.HOME:
        await state.clear()
        await ensure_root(bot, chat_id, user_id, HOME_TEXT, home_keyboard(user_id in settings.admin_ids()))
        return

    if action == callbacks.BUY:
        await _render_plan_list(bot, chat_id, user_id)
        return

    if action == callbacks.BUY_PLAN:
        if not parts:
            await _render_plan_list(bot, chat_id, user_id)
            return
        plan_code = parts[0]
        await state.update_data(plan_code=plan_code)
        async with SessionLocal() as session:
            locations = await list_locations(session)
        buttons = [
            [InlineKeyboardButton(text=loc.title, callback_data=callbacks.pack(callbacks.BUY_LOCATION, loc.code))]
            for loc in locations
        ]
        buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)])
        await ensure_root(
            bot,
            chat_id,
            user_id,
            "Выберите локацию:",
            InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        return

    if action == callbacks.BUY_LOCATION:
        if not parts:
            return
        location_code = parts[0]
        data = await state.get_data()
        await state.update_data(location_code=location_code)
        async with SessionLocal() as session:
            user = await get_user(session, user_id)
            plan = await get_plan(session, data.get("plan_code")) if data.get("plan_code") else None
            location = next((loc for loc in await list_locations(session) if loc.code == location_code), None)
        amount = plan.price_stars if plan else 0
        discount = data.get("discount_stars", 0)
        free_days = data.get("free_days", 0)
        summary = _format_buy_summary(plan, location, max(amount - discount, 1), discount, free_days)
        include_trial = user is not None and user.trial_used_at is None
        await ensure_root(bot, chat_id, user_id, summary, buy_keyboard(include_trial))
        return

    if action == callbacks.BUY_PROMO:
        await state.set_state(UserFlow.awaiting_promo)
        await ensure_root(bot, chat_id, user_id, PROMO_TEXT, back_home_keyboard())
        return

    if action == callbacks.BUY_TRIAL:
        async with SessionLocal() as session:
            user = await get_user(session, user_id)
            if not user or user.trial_used_at:
                await ensure_root(bot, chat_id, user_id, TRIAL_USED_TEXT, back_home_keyboard())
                return
            data = await state.get_data()
            plan_code = data.get("plan_code") or "classic"
            location_code = data.get("location_code") or "nl1"
            job = JobOutbox(
                job_type="provision_subscription",
                payload={
                    "user_id": user_id,
                    "plan_code": plan_code,
                    "location_code": location_code,
                    "period_days": 1,
                    "source": "trial",
                },
                status="pending",
                idempotency_key=f"trial:{user_id}",
            )
            await enqueue_job_safe(session, job)
            await mark_trial_used(session, user_id, utcnow())
        await ensure_root(bot, chat_id, user_id, PAYMENT_SUCCESS_TEXT, back_home_keyboard())
        return

    if action == callbacks.BUY_PAY:
        data = await state.get_data()
        if not data.get("plan_code") or not data.get("location_code"):
            await ensure_root(bot, chat_id, user_id, "Сначала выберите тариф и локацию.", back_home_keyboard())
            return
        async with SessionLocal() as session:
            plan = await get_plan(session, data["plan_code"])
            location = next((loc for loc in await list_locations(session) if loc.code == data["location_code"]), None)
            if not plan or not location:
                await ensure_root(bot, chat_id, user_id, "Не удалось загрузить тариф или локацию.", back_home_keyboard())
                return
            discount = int(data.get("discount_stars", 0))
            amount = max(plan.price_stars - discount, 1)
            service = PaymentService(StarsProvider())
            intent = await service.create_intent(
                session,
                user_id=user_id,
                plan_code=plan.plan_code,
                period_days=plan.duration_days,
                location_code=location.code,
                amount_stars=amount,
                promo_code_id=data.get("promo_code_id"),
            )
            if data.get("free_days"):
                intent.meta["free_days"] = int(data["free_days"])
            await session.commit()
            invoice = service.provider.create_invoice(str(intent.id), amount, f"{plan.title} • {location.title}")
        await bot.send_invoice(
            chat_id=user_id,
            title=invoice.title,
            description=invoice.description,
            payload=invoice.payload,
            provider_token="",
            currency=invoice.currency,
            prices=invoice.prices,
        )
        await ensure_root(bot, chat_id, user_id, "Счёт отправлен в чат Telegram Stars.", back_home_keyboard())
        return

    if action == callbacks.SUBSCRIPTIONS:
        async with SessionLocal() as session:
            subs = await list_user_subscriptions(session, user_id)
        if not subs:
            await ensure_root(bot, chat_id, user_id, "Подписок пока нет.", back_home_keyboard())
            return
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"{sub.plan_code.upper()} • {sub.location_code} • {sub.status}",
                    callback_data=callbacks.pack(callbacks.SUB_VIEW, str(sub.id)),
                )
            ]
            for sub in subs
        ]
        buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)])
        await ensure_root(bot, chat_id, user_id, SUBSCRIPTIONS_TEXT, InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    if action == callbacks.SUB_VIEW and parts:
        sub_id = int(parts[0])
        async with SessionLocal() as session:
            sub = await get_subscription(session, sub_id, user_id)
        if not sub:
            await ensure_root(bot, chat_id, user_id, "Подписка не найдена.", back_home_keyboard())
            return
        text = (
            f"Подписка #{sub.id}\n"
            f"Тариф: {sub.plan_code}\n"
            f"Локация: {sub.location_code}\n"
            f"Статус: {sub.status}\n"
            f"Действует до: {sub.expires_at:%Y-%m-%d %H:%M}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Получить ссылку", callback_data=callbacks.pack(callbacks.SUB_LINK, str(sub.id)))],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=callbacks.SUBSCRIPTIONS)],
            ]
        )
        await ensure_root(bot, chat_id, user_id, text, keyboard)
        return

    if action == callbacks.SUB_LINK and parts:
        sub_id = int(parts[0])
        async with SessionLocal() as session:
            sub = await get_subscription(session, sub_id, user_id)
            if not sub:
                await ensure_root(bot, chat_id, user_id, "Подписка не найдена.", back_home_keyboard())
                return
            job = JobOutbox(
                job_type="send_notifications",
                payload={"kind": "delivery_link", "user_id": user_id, "subscription_id": sub_id},
                status="pending",
                idempotency_key=f"delivery:{sub_id}",
            )
            await enqueue_job_safe(session, job)
        await ensure_root(bot, chat_id, user_id, "Запрос на ссылку принят. Ответ придёт в чат.", back_home_keyboard())
        return

    if action == callbacks.DEVICES:
        await ensure_root(bot, chat_id, user_id, DEVICE_GUIDE_TEXT, back_home_keyboard())
        return

    if action == callbacks.ADGUARD:
        async with SessionLocal() as session:
            user = await get_user(session, user_id)
        enabled = bool(user and user.adguard_enabled)
        text = ADGUARD_TEXT.format(primary=settings.adguard_dns_primary, secondary=settings.adguard_dns_secondary)
        toggle_text = "Отключить" if enabled else "Включить"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{toggle_text} AdGuard", callback_data=callbacks.ADGUARD_TOGGLE)],
                [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)],
            ]
        )
        await ensure_root(bot, chat_id, user_id, text, keyboard)
        return

    if action == callbacks.ADGUARD_TOGGLE:
        async with SessionLocal() as session:
            user = await get_user(session, user_id)
            if user:
                await set_adguard(session, user_id, not user.adguard_enabled)
        await ensure_root(bot, chat_id, user_id, "Настройка AdGuard обновлена.", back_home_keyboard())
        return

    if action == callbacks.REFERRAL:
        async with SessionLocal() as session:
            user = await get_user(session, user_id)
        bot_me = await bot.get_me()
        link = f"https://t.me/{bot_me.username}?start=ref_{user.ref_code}" if user else "-"
        await ensure_root(bot, chat_id, user_id, REFERRAL_TEXT.format(link=link), back_home_keyboard())
        return

    if action == callbacks.PROMO:
        await state.set_state(UserFlow.awaiting_promo)
        await ensure_root(bot, chat_id, user_id, PROMO_TEXT, back_home_keyboard())
        return

    if action == callbacks.SUPPORT:
        await ensure_root(bot, chat_id, user_id, SUPPORT_TEXT, support_keyboard())
        return

    if action == callbacks.SUPPORT_NEW:
        await state.set_state(UserFlow.awaiting_support_message)
        await ensure_root(bot, chat_id, user_id, "Опишите проблему в одном сообщении.", back_home_keyboard())
        return

    if action == callbacks.SUPPORT_LIST:
        async with SessionLocal() as session:
            tickets = await list_tickets(session, user_id)
        if not tickets:
            await ensure_root(bot, chat_id, user_id, "Обращений пока нет.", back_home_keyboard())
            return
        buttons = [
            [InlineKeyboardButton(text=f"#{ticket.id} • {ticket.status}", callback_data=callbacks.pack(callbacks.SUPPORT_VIEW, str(ticket.id)))]
            for ticket in tickets
        ]
        buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)])
        await ensure_root(bot, chat_id, user_id, "Ваши обращения:", InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    if action == callbacks.SUPPORT_VIEW and parts:
        ticket_id = int(parts[0])
        async with SessionLocal() as session:
            ticket = await get_ticket(session, ticket_id, user_id)
            messages = await list_ticket_messages(session, ticket_id)
        if not ticket:
            await ensure_root(bot, chat_id, user_id, "Обращение не найдено.", back_home_keyboard())
            return
        history = "\n".join([f"{msg.sender_tg_id}: {msg.body}" for msg in messages[-5:]]) or "Сообщений пока нет."
        text = f"Тикет #{ticket.id} ({ticket.status})\n\n{history}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Ответить", callback_data=callbacks.pack(callbacks.SUPPORT_REPLY, str(ticket.id)))],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=callbacks.SUPPORT_LIST)],
            ]
        )
        await ensure_root(bot, chat_id, user_id, text, keyboard)
        return

    if action == callbacks.SUPPORT_REPLY and parts:
        await state.set_state(UserFlow.awaiting_ticket_reply)
        await state.update_data(ticket_id=int(parts[0]))
        await ensure_root(bot, chat_id, user_id, "Напишите ответ в одном сообщении.", back_home_keyboard())
        return

    if action == callbacks.ADMIN and user_id in settings.admin_ids():
        await ensure_root(bot, chat_id, user_id, ADMIN_TEXT, admin_keyboard())
        return

    if action in {callbacks.ADMIN_SYNC_SERVERS, callbacks.ADMIN_SYNC_USERS, callbacks.ADMIN_RECONCILE} and user_id in settings.admin_ids():
        job_type = {
            callbacks.ADMIN_SYNC_SERVERS: "sync_servers",
            callbacks.ADMIN_SYNC_USERS: "sync_users",
            callbacks.ADMIN_RECONCILE: "reconcile",
        }[action]
        async with SessionLocal() as session:
            job = JobOutbox(
                job_type=job_type,
                payload={"actor": user_id},
                status="pending",
                idempotency_key=f"{job_type}:{utcnow().date().isoformat()}",
            )
            await enqueue_job_safe(session, job)
        await ensure_root(bot, chat_id, user_id, "Задача поставлена в очередь.", back_home_keyboard())
        return

    if action == callbacks.ADMIN_TICKETS and user_id in settings.admin_ids():
        async with SessionLocal() as session:
            tickets = await list_tickets(session, user_id=None)
        if not tickets:
            await ensure_root(bot, chat_id, user_id, "Тикетов нет.", back_home_keyboard())
            return
        buttons = [
            [InlineKeyboardButton(text=f"#{ticket.id} • {ticket.status}", callback_data=callbacks.pack(callbacks.ADMIN_TICKET_VIEW, str(ticket.id)))]
            for ticket in tickets[:20]
        ]
        buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)])
        await ensure_root(bot, chat_id, user_id, "Список тикетов:", InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    if action == callbacks.ADMIN_TICKET_VIEW and parts and user_id in settings.admin_ids():
        ticket_id = int(parts[0])
        async with SessionLocal() as session:
            ticket = await get_ticket(session, ticket_id, user_id=None)
            messages = await list_ticket_messages(session, ticket_id)
        if not ticket:
            await ensure_root(bot, chat_id, user_id, "Тикет не найден.", back_home_keyboard())
            return
        history = "\n".join([f"{msg.sender_tg_id}: {msg.body}" for msg in messages[-5:]]) or "Сообщений пока нет."
        text = f"Тикет #{ticket.id} (user {ticket.user_id})\n\n{history}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Ответить", callback_data=callbacks.pack(callbacks.ADMIN_TICKET_REPLY, str(ticket.id)))],
                [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)],
            ]
        )
        await ensure_root(bot, chat_id, user_id, text, keyboard)
        return

    if action == callbacks.FAQ:
        await _render_content_page(bot, chat_id, user_id, "faq", FAQ_TEXT)
        return
    if action == callbacks.OFFER:
        await _render_content_page(bot, chat_id, user_id, "offer", OFFER_TEXT)
        return
    if action == callbacks.PRIVACY:
        await _render_content_page(bot, chat_id, user_id, "privacy", PRIVACY_TEXT)
        return
    if action == callbacks.TERMS:
        await _render_content_page(bot, chat_id, user_id, "terms", TERMS_TEXT)
        return


@router.message(UserFlow.awaiting_promo)
async def promo_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    if not message.text:
        return
    code = message.text.strip().upper()
    async with SessionLocal() as session:
        promo = await get_promo(session, code)
        if not promo:
            await ensure_root(bot, message.chat.id, message.from_user.id, "Промокод не найден.", back_home_keyboard())
            await state.clear()
            return
        if await has_redemption(session, promo.id, message.from_user.id):
            await ensure_root(bot, message.chat.id, message.from_user.id, "Промокод уже использован.", back_home_keyboard())
            await state.clear()
            return
        if promo.max_redemptions:
            total = await count_redemptions(session, promo.id)
            if total >= promo.max_redemptions:
                await ensure_root(bot, message.chat.id, message.from_user.id, "Лимит промокода исчерпан.", back_home_keyboard())
                await state.clear()
                return
        data = await state.get_data()
        plan = await get_plan(session, data.get("plan_code")) if data.get("plan_code") else None
        amount = plan.price_stars if plan else 0
        discount, free_days = _promo_discount(amount, promo)
        data.update(
            promo_code_id=promo.id,
            promo_code=promo.code,
            discount_stars=discount,
            free_days=free_days,
        )
    await state.clear()
    await state.set_data(data)
    await ensure_root(
        bot,
        message.chat.id,
        message.from_user.id,
        PROMO_APPLIED_TEXT.format(discount=discount, free_days=free_days),
        back_home_keyboard(),
    )


@router.message(UserFlow.awaiting_support_message)
async def support_message_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    if not message.text:
        return
    if not await rate_limit(message.from_user.id, "support", limit_seconds=30):
        await ensure_root(bot, message.chat.id, message.from_user.id, "Пожалуйста, подождите перед новым обращением.", back_home_keyboard())
        return
    async with SessionLocal() as session:
        ticket = await create_ticket(session, message.from_user.id, status="open")
        await add_message(session, ticket.id, message.from_user.id, message.text.strip())
    await state.clear()
    await ensure_root(bot, message.chat.id, message.from_user.id, f"Тикет #{ticket.id} создан.", support_keyboard())


@router.message(UserFlow.awaiting_ticket_reply)
async def support_reply_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    if not message.text:
        return
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    async with SessionLocal() as session:
        ticket = await get_ticket(session, ticket_id, user_id=message.from_user.id)
        if not ticket:
            await ensure_root(bot, message.chat.id, message.from_user.id, "Тикет не найден.", back_home_keyboard())
            await state.clear()
            return
        await add_message(session, ticket_id, message.from_user.id, message.text.strip())
        await update_ticket_status(session, ticket, "open")
    await state.clear()
    await ensure_root(bot, message.chat.id, message.from_user.id, "Сообщение отправлено в поддержку.", support_keyboard())


@router.message(UserFlow.awaiting_admin_reply)
async def admin_reply_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    if not message.text:
        return
    if message.from_user.id not in settings.admin_ids():
        await state.clear()
        return
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    async with SessionLocal() as session:
        ticket = await get_ticket(session, ticket_id, user_id=None)
        if not ticket:
            await ensure_root(bot, message.chat.id, message.from_user.id, "Тикет не найден.", back_home_keyboard())
            await state.clear()
            return
        await add_message(session, ticket_id, message.from_user.id, message.text.strip())
        await update_ticket_status(session, ticket, "answered")
        job = JobOutbox(
            job_type="send_notifications",
            payload={"kind": "support_reply", "user_id": ticket.user_id, "text": message.text.strip()},
            status="pending",
            idempotency_key=f"support_reply:{ticket.id}:{message.message_id}",
        )
        await enqueue_job_safe(session, job)
    await state.clear()
    await ensure_root(bot, message.chat.id, message.from_user.id, "Ответ отправлен пользователю.", admin_keyboard())
    if action == callbacks.ADMIN_TICKET_REPLY and parts and user_id in settings.admin_ids():
        await state.set_state(UserFlow.awaiting_admin_reply)
        await state.update_data(ticket_id=int(parts[0]))
        await ensure_root(bot, chat_id, user_id, "Введите ответ пользователю.", back_home_keyboard())
        return
