from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard(is_admin: bool, best_access: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⚡ AmneziaWG", callback_data="awg")],
        [InlineKeyboardButton(text="🌐 Neyra Basic", callback_data="public")],
        [InlineKeyboardButton(text="⭐ Лучшие ключи", callback_data="best")],
        [InlineKeyboardButton(text="📱 Как подключить", callback_data="help")],
    ]
    if best_access:
        rows.insert(2, [InlineKeyboardButton(text="⭐ Neyra Best", callback_data="best_sub")])
    if is_admin:
        rows.append([InlineKeyboardButton(text="👑 Neyra Creator", callback_data="creator")])
        rows.append([InlineKeyboardButton(text="📊 Статус Neyra", callback_data="admin_status")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def access_request_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выдать доступ", callback_data=f"grant:{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"deny:{user_id}"),
        ]
    ])
