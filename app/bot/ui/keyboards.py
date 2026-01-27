from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.ui import callbacks


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить подписку", callback_data=callbacks.BUY)],
            [InlineKeyboardButton(text="👤 ЛК", callback_data=callbacks.SUBSCRIPTIONS)],
            [InlineKeyboardButton(text="📚 Инструкции", callback_data=callbacks.DEVICES)],
            [InlineKeyboardButton(text="🆘 Поддержка", callback_data=callbacks.SUPPORT)],
        ]
    )
