"""
bot/handlers/callbacks.py — Post confirm/cancel callbacks with new UI.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import CallbackQuery

from bot.services.post_builder import build_and_post
from bot.utils.admin import is_admin
from bot.utils import fsm
from bot.ui import messages, keyboards
from config import config

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(CallbackQueryHandler(
        _post_callback,
        filters.regex(r"^(confirm_post|cancel_post):\d+$"),
    ))
    client.add_handler(CallbackQueryHandler(
        _post_step_callback,
        filters.regex(r"^post:"),
    ))
    client.add_handler(CallbackQueryHandler(
        _channel_callback,
        filters.regex(r"^ch:"),
    ))
    client.add_handler(CallbackQueryHandler(
        _step_callback,
        filters.regex(r"^step:"),
    ))


async def _post_callback(client: Client, query: CallbackQuery) -> None:
    uid = query.from_user.id
    if not is_admin(uid):
        await query.answer("admin only", show_alert=True)
        return

    action, owner_uid_str = query.data.split(":", 1)
    if uid != int(owner_uid_str):
        await query.answer("not your session", show_alert=True)
        return

    if action == "cancel_post":
        fsm.clear(uid)
        await query.message.edit_text(
            messages.post_cancelled(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.back_to_main(),
        )
        await query.answer()
        return

    state = fsm.get_state(uid)
    if state != fsm.AWAIT_CONFIRM:
        await query.answer("session expired", show_alert=True)
        return

    data = fsm.get_data(uid)
    await query.message.edit_text(
        messages.post_publishing(),
        parse_mode=enums.ParseMode.HTML,
    )
    await query.answer()

    deep_link_id = await build_and_post(client, data)
    fsm.clear(uid)

    if deep_link_id:
        bot_link = f"https://t.me/{config.BOT_USERNAME}?start={deep_link_id}"
        await query.message.edit_text(
            messages.post_published(bot_link),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.back_to_main(),
        )
    else:
        await query.message.edit_text(
            messages.post_failed(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.back_to_main(),
        )


async def _post_step_callback(client: Client, query: CallbackQuery) -> None:
    if not is_admin(query.from_user.id):
        await query.answer("admin only", show_alert=True)
        return

    action = query.data.split(":")[1]
    await query.answer()

    if action == "start":
        await query.message.edit_text(
            messages.post_creator(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.post_creator_menu(),
        )


async def _channel_callback(client: Client, query: CallbackQuery) -> None:
    if not is_admin(query.from_user.id):
        await query.answer("admin only", show_alert=True)
        return

    action = query.data.split(":")[1]
    await query.answer()

    if action == "add":
        from bot.utils import fsm
        fsm.set_state(query.from_user.id, fsm.AWAIT_CHANNEL)
        await query.message.edit_text(
            messages.channel_set_prompt(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.back_to_main(),
        )
    else:
        from bot.database.crud import get_main_channel
        channel_id = await get_main_channel()
        await query.message.edit_text(
            messages.channel_dashboard(channel_id),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.channel_menu(),
        )


async def _step_callback(client: Client, query: CallbackQuery) -> None:
    """Handle skip/cancel inline buttons during post flow."""
    if not is_admin(query.from_user.id):
        await query.answer("admin only", show_alert=True)
        return

    action = query.data.split(":")[1]
    uid = query.from_user.id
    await query.answer()

    if action == "cancel":
        fsm.clear(uid)
        await query.message.edit_text(
            messages.post_cancelled(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.back_to_main(),
        )

    elif action == "skip":
        state = fsm.get_state(uid)

        if state == fsm.AWAIT_MEDIA:
            fsm.set_state(uid, fsm.AWAIT_480P)
            await query.message.edit_text(
                messages.post_quality_prompt("480p"),
                parse_mode=enums.ParseMode.HTML,
                reply_markup=keyboards.skip_cancel_row(),
            )

        elif state in fsm.QUALITY_STATES:
            label = fsm.quality_label_for_state(state)
            next_state = fsm.NEXT_QUALITY_STATE[state]

            if next_state == fsm.AWAIT_CONFIRM:
                fsm.set_state(uid, fsm.AWAIT_CONFIRM)
                data = fsm.get_data(uid)
                anime = data["anime_info"]
                qualities = data.get("qualities", {})
                episode = data.get("episode", "?")
                custom_media = data.get("custom_media")
                custom_media_type = data.get("custom_media_type")
                media_source = f"custom {custom_media_type}" if custom_media else "auto card"

                await query.message.edit_text(
                    messages.post_preview(anime, episode, qualities, media_source),
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=keyboards.post_confirm_menu(uid),
                )
            else:
                fsm.set_state(uid, next_state)
                next_label = fsm.quality_label_for_state(next_state)
                await query.message.edit_text(
                    messages.post_skipped(label, next_label),
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=keyboards.skip_cancel_row(),
                )
        else:
            await query.message.edit_text(
                messages.nothing_to_skip(),
                parse_mode=enums.ParseMode.HTML,
                reply_markup=keyboards.back_to_main(),
            )
