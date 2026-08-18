from __future__ import annotations

import logging

from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.types import BufferedInputFile

from app.bot.keyboards import access_request_keyboard, main_keyboard
from app.config import Settings
from app.services.amneziawg import build_config, register
from app.services.subscription import AccessStore, SubscriptionService

log = logging.getLogger(__name__)
router = Router()
access = AccessStore()


def is_admin(settings: Settings, user_id: int | None) -> bool:
    return bool(user_id and settings.admin_user_id and str(user_id) == settings.admin_user_id)


def has_best(settings: Settings, user_id: int | None) -> bool:
    return bool(user_id and (is_admin(settings, user_id) or access.has_access(user_id)))


@router.message(CommandStart())
async def start(message: types.Message, settings: Settings) -> None:
    uid = message.from_user.id if message.from_user else None
    await message.answer(
        "👋 <b>Neyra VPN</b>\n\nВыбери уровень подключения:",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(settings, uid), has_best(settings, uid)),
    )


@router.callback_query(F.data == "awg")
async def awg(callback: types.CallbackQuery, settings: Settings) -> None:
    await callback.answer("Готовлю AmneziaWG…")
    try:
        data = await register()
        document = BufferedInputFile(build_config(data).encode(), filename="Neyra_AmneziaWG.conf")
        await callback.message.answer_document(
            document=document,
            caption="⚡ <b>Neyra AmneziaWG</b>\n\nНовый конфиг готов.",
            parse_mode="HTML",
            reply_markup=main_keyboard(is_admin(settings, callback.from_user.id), has_best(settings, callback.from_user.id)),
        )
    except Exception:
        log.exception("AmneziaWG generation failed")
        await callback.message.answer("❌ Не удалось получить новый конфиг. Попробуй позже.")


@router.callback_query(F.data == "public")
async def public_sub(callback: types.CallbackQuery, settings: Settings) -> None:
    await callback.answer()
    await callback.message.answer(
        "🌐 <b>Neyra Basic</b>\n\n"
        f"<code>{settings.subscription_url}</code>\n\n"
        "Это постоянно обновляемая подписка. Добавь её в Happ/2RayTun/v2rayNG/Hiddify.",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(settings, callback.from_user.id), has_best(settings, callback.from_user.id)),
    )


@router.callback_query(F.data == "best")
async def best_request(callback: types.CallbackQuery, settings: Settings) -> None:
    uid = callback.from_user.id
    if has_best(settings, uid):
        await callback.answer("Доступ уже есть")
        await best_sub(callback, settings, edit=False)
        return
    changed = access.request(uid)
    await callback.answer("Запрос отправлен" if changed else "Запрос уже ожидает", show_alert=True)
    if changed and settings.admin_user_id:
        try:
            await callback.bot.send_message(
                int(settings.admin_user_id),
                "🔐 <b>Запрос доступа к Neyra Best</b>\n\n"
                f"Пользователь: <code>{uid}</code>\n"
                f"Имя: {callback.from_user.full_name}",
                parse_mode="HTML",
                reply_markup=access_request_keyboard(uid),
            )
        except Exception:
            log.exception("Failed to notify admin about access request")
    await callback.message.answer("⏳ Запрос на доступ к лучшему пулу отправлен создателю.")


@router.callback_query(F.data == "best_sub")
async def best_sub(callback: types.CallbackQuery, settings: Settings, edit: bool = True) -> None:
    if not has_best(settings, callback.from_user.id):
        await callback.answer("Сначала запроси доступ.", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        "⭐ <b>Neyra Best</b>\n\n"
        f"<code>{settings.best_url}</code>\n\n"
        "Это отобранный пул с более высоким рейтингом конфигураций.",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(settings, callback.from_user.id), True),
    )


@router.callback_query(F.data == "creator")
async def creator(callback: types.CallbackQuery, settings: Settings) -> None:
    if not is_admin(settings, callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        "👑 <b>Neyra Creator</b>\n\n"
        f"<code>{settings.creator_url}</code>\n\n"
        "Твой отдельный пул с максимальным лимитом лучших узлов.",
        parse_mode="HTML",
        reply_markup=main_keyboard(True, True),
    )


@router.callback_query(F.data.startswith("grant:"))
async def grant(callback: types.CallbackQuery, settings: Settings) -> None:
    if not is_admin(settings, callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    uid = int(callback.data.split(":", 1)[1])
    access.approve(uid)
    await callback.answer("Доступ выдан")
    try:
        await callback.bot.send_message(uid, "⭐ <b>Neyra Best</b>\n\nДоступ одобрен. Открой /start.", parse_mode="HTML")
    except Exception:
        log.exception("Failed to notify approved user")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("deny:"))
async def deny(callback: types.CallbackQuery, settings: Settings) -> None:
    if not is_admin(settings, callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    uid = int(callback.data.split(":", 1)[1])
    access.deny(uid)
    await callback.answer("Запрос отклонён")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data == "help")
async def help_handler(callback: types.CallbackQuery, settings: Settings) -> None:
    await callback.answer()
    await callback.message.answer(
        "📖 <b>Как подключить</b>\n\n"
        "⚡ AmneziaWG — импортируй .conf.\n\n"
        "🌐 Подписки Neyra — добавь URL в Happ/2RayTun/v2rayNG/Hiddify.\n"
        "Happ поддерживает автообновление подписки через параметры, которые Neyra добавляет в её тело.",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(settings, callback.from_user.id), has_best(settings, callback.from_user.id)),
    )


@router.callback_query(F.data == "admin_status")
async def admin_status(callback: types.CallbackQuery, settings: Settings) -> None:
    if not is_admin(settings, callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await callback.answer("Проверяю…")
    service = SubscriptionService(settings.subscription_url, settings.stats_url, settings.best_url, settings.creator_url)
    stats = await service.stats()
    if not stats:
        text = "👑 <b>NEYRA STATUS</b>\n\n🟢 Bot: ONLINE\n🔴 Subscription: UNAVAILABLE"
    else:
        text = (
            "👑 <b>NEYRA STATUS</b>\n\n🟢 Bot: ONLINE\n🟢 Subscription: HEALTHY\n"
            f"📦 Nodes: <b>{stats.get('nodes', 0)}</b>\n"
            f"⭐ Best: <b>{stats.get('best_nodes', 0)}</b>\n"
            f"👑 Creator: <b>{stats.get('creator_nodes', 0)}</b>\n"
            f"🟢 Sources OK: {stats.get('sources_ok', 0)}\n"
            f"🔴 Sources failed: {stats.get('sources_failed', 0)}\n"
            f"🕐 Last build: <code>{stats.get('generated_at', 'unknown')}</code>"
        )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=main_keyboard(True, True))
