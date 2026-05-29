"""
bot/handlers/text_router.py — Single unified text message router.

All FSM text handling goes through here to avoid handler conflicts.
Checks state and routes to the correct handler.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.utils import fsm
from bot.utils.admin import is_admin
from bot.database.crud import set_template, set_main_channel

log = logging.getLogger(__name__)

IGNORED_COMMANDS = [
    "start", "cancel", "skip", "setmainchannel",
    "settemplate", "gettemplate", "settings", "post",
    "broadcast", "cancelbroadcast", "users"
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

    # ── Template saving ───────────────────────────────────────────────────────
    if state == fsm.AWAIT_TEMPLATE:
        await _handle_template(message, uid)
        return

    # ── Channel ID input ──────────────────────────────────────────────────────
    if state == fsm.AWAIT_CHANNEL:
        await _handle_channel_id(message, uid)
        return

    # ── Broadcast text ────────────────────────────────────────────────────────
    if state == fsm.AWAIT_BROADCAST:
        # Handled by broadcast.py media handler — text goes there too
        from bot.handlers.broadcast import _do_broadcast
        await _do_broadcast(client, message, uid)
        return

    # ── Quality link input ────────────────────────────────────────────────────
    if state in fsm.QUALITY_STATES:
        await _handle_quality_link(client, message, uid, state)
        return


async def _handle_template(message: Message, uid: int) -> None:
    """Save template text to MongoDB."""
    text = message.text

    if "{cover_image}" in text:
        await message.reply(
            "⚠️ Remove <code>{cover_image}</code> from your template.\n"
            "The cover image is sent automatically — it cannot go in caption text.\n\n"
            "Send the template again without it.",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    data = fsm.get_data(uid)
    template_name = data.get("template_name")

    if not template_name:
        await message.reply("⚠️ Session expired. Use /settemplate again.")
        fsm.clear(uid)
        return

    await set_template(template_name, text)
    fsm.clear(uid)
    await message.reply(
        f"✅ Template <b>{template_name}</b> saved!",
        parse_mode=enums.ParseMode.HTML,
    )


async def _handle_channel_id(message: Message, uid: int) -> None:
    """Save channel ID from text input."""
    try:
        channel_id = int(message.text.strip())
        await set_main_channel(channel_id)
        fsm.clear(uid)
        await message.reply(
            f"✅ Main channel set to <code>{channel_id}</code>.",
            parse_mode=enums.ParseMode.HTML,
        )
    except ValueError:
        await message.reply(
            "⚠️ Invalid channel ID. Send a number like <code>-1001234567890</code>",
            parse_mode=enums.ParseMode.HTML,
        )


async def _handle_quality_link(client: Client, message: Message, uid: int, state: str) -> None:
    """Save quality link and advance FSM."""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from bot.utils.html import escape_html, SEPARATOR

    link = message.text.strip()
    if not (link.startswith("http://") or link.startswith("https://") or link.startswith("tg://")):
        await message.reply("⚠️ That doesn't look like a valid URL. Send a link or /skip.", quote=True)
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
            f"✅ Saved {label}.\n\n"
            f"📎 Send the <b>{next_label.upper()}</b> link, /skip, or /cancel.",
            parse_mode=enums.ParseMode.HTML,
            quote=True,
        )


async def _send_preview(message: Message, uid: int) -> None:
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from bot.utils.html import escape_html, SEPARATOR

    data = fsm.get_data(uid)
    anime = data["anime_info"]
    qualities = data.get("qualities", {})
    episode = data.get("episode", "?")
    custom_media = data.get("custom_media")
    custom_media_type = data.get("custom_media_type")

    quality_text = "\n".join(f"  • {k}" for k in qualities.keys()) if qualities else "  • (none)"
    media_source = f"Custom {custom_media_type}" if custom_media else "AniList cover / Auto card"

    preview = (
        f"<b>📋 Preview</b>\n{SEPARATOR}\n\n"
        f"<b>{escape_html(anime['title_romaji'])}</b>\n"
        f"<i>{escape_html(anime['title_english'])}</i>\n\n"
        f"<b>Episode:</b> {escape_html(str(episode))}\n"
        f"<b>Season:</b> {escape_html(str(anime['season']))}\n"
        f"<b>Media:</b> {media_source}\n\n"
        f"<b>Qualities:</b>\n{escape_html(quality_text)}\n\n"
        f"{SEPARATOR}\n<i>Confirm to post to channel?</i>"
    )

    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Post Now", callback_data=f"confirm_post:{uid}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_post:{uid}"),
    ]])

    await message.reply(preview, parse_mode=enums.ParseMode.HTML, reply_markup=markup, quote=True)
