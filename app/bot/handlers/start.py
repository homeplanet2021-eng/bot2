from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.ui import callbacks
from app.bot.ui.keyboards import home_keyboard
from app.bot.ui.texts import HOME_TEXT
from app.common.redis import user_lock
from app.db.session import SessionLocal
from app.db.repos.users import create_user, get_user, get_user_by_ref_code

router = Router()

ROOT_MESSAGE: dict[int, int] = {}


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot) -> None:
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

    if message.from_user.id in ROOT_MESSAGE:
        await bot.edit_message_text(
            text=HOME_TEXT,
            chat_id=message.chat.id,
            message_id=ROOT_MESSAGE[message.from_user.id],
            reply_markup=home_keyboard(),
        )
    else:
        sent = await message.answer(HOME_TEXT, reply_markup=home_keyboard())
        ROOT_MESSAGE[message.from_user.id] = sent.message_id


@router.callback_query()
async def callback_handler(query: CallbackQuery, bot: Bot) -> None:
    await query.answer("Готово")
    if not query.message:
        return
    await bot.edit_message_text(
        text=HOME_TEXT,
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=home_keyboard(),
    )
