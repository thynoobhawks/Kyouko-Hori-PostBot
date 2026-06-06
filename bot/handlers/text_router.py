"""
bot/handlers/text_router.py — Unified text router with new UI.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.utils import fsm
from bot.utils.admin import is_admin
from bot.database.crud import set_template, set_main_channel
from bot.ui import messages, keyboards

log = logging.getLogger(__name__)

IGNORED_COMMANDS = [
    "start", "cancel", "skip", "setmainchannel",
    "settemplate", "gettemplate", "settings", "post",
    "broadcast", "cancelbroadcast", "users", "menu"
]


def register(client: Client) -> None:
    client.add_handler(MessageHandler(
        _unified_text_router,
        filters.text & filters.private & ~filters.command(IGNORED_COMMANDS),
    ))


async def _unified_text_router(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return

    state = fsm.get_state(uid)

    if state == fsm.AWAIT_TEMPLATE:
        await _handle_template(message, uid)
    elif state == fsm.AWAIT_CHANNEL:
        await _handle_channel_id(message, uid)
    elif state == fsm.AWAIT_BROADCAST:
        from bot.handlers.broadcast import _do_broadcast
        await _do_broadcast(client, message, uid)
    elif state in fsm.QUALITY_STATES:
        await _handle_quality_link(message, uid, state)


async def _handle_template(message: Message, uid: int) -> None:
    if "{cover_image}" in message.text:
        await message.reply(
            messages.error("remove {cover_image} from template — image is sent automatically"),
            parse_mode=enums.ParseMode.HTML,
        )
        return

    data = fsm.get_data(uid)
    template_name = data.get("template_name")
    if not template_name:
        await message.reply(messages.error("session expired — use /settemplate again"), parse_mode=enums.ParseMode.HTML)
        fsm.clear(uid)
        return

    await set_template(template_name, message.text)
    fsm.clear(uid)
    await message.reply(
        messages.template_saved(template_name),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.template_menu(),
    )


async def _handle_channel_id(message: Message, uid: int) -> None:
    try:
        channel_id = int(message.text.strip())
        await set_main_channel(channel_id)
        fsm.clear(uid)
        await message.reply(
            messages.channel_saved(channel_id),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.channel_menu(),
        )
    except ValueError:
        await message.reply(
            messages.error("invalid id — send a number like -1001234567890"),
            parse_mode=enums.ParseMode.HTML,
        )


async def _handle_quality_link(message: Message, uid: int, state: str) -> None:
    link = message.text.strip()
    if not (link.startswith("http://") or link.startswith("https://") or link.startswith("tg://")):
        await message.reply(
            messages.error("that doesn't look like a valid url — send a link or skip"),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.skip_cancel_row(),
        )
        return

    label = fsm.quality_label_for_state(state)
    data = fsm.get_data(uid)
    data["qualities"][label] = link
    next_state = fsm.NEXT_QUALITY_STATE[state]

    if next_state == fsm.AWAIT_CONFIRM:
        fsm.set_state(uid, fsm.AWAIT_CONFIRM, data)
        await _send_preview(message, uid)
    else:
        fsm.set_state(uid, next_state, data)
        next_label = fsm.quality_label_for_state(next_state)
        await message.reply(
            messages.post_quality_saved(label, next_label),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.skip_cancel_row(),
            quote=True,
        )


async def _send_preview(message: Message, uid: int) -> None:
    data = fsm.get_data(uid)
    anime = data["anime_info"]
    qualities = data.get("qualities", {})
    episode = data.get("episode", "?")
    custom_media = data.get("custom_media")
    custom_media_type = data.get("custom_media_type")
    media_source = f"custom {custom_media_type}" if custom_media else "auto card"

    await message.reply(
        messages.post_preview(anime, episode, qualities, media_source),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.post_confirm_menu(uid),
        quote=True,
    )

