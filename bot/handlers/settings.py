"""
bot/handlers/settings.py — Admin settings commands.

Commands:
  /setmainchannel  — set the channel to post to
  /settemplate     — update a post template
  /gettemplate     — view current template
  /settings        — show current settings summary
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.database.crud import (
    set_main_channel,
    get_main_channel,
    get_template,
    set_template,
)
from bot.utils.admin import is_admin
from bot.utils.html import escape_html, code
from bot.utils import fsm

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(filters.command("setmainchannel") & filters.private, _set_channel)
    client.add_handler(filters.command("settings") & filters.private, _show_settings)
    client.add_handler(filters.command("settemplate") & filters.private, _set_template_cmd)
    client.add_handler(filters.command("gettemplate") & filters.private, _get_template_cmd)

    # Handle channel message forwarded for channel ID detection
    client.add_handler(
        filters.forwarded & filters.private,
        _forwarded_channel_handler,
        group=2,
    )


# ── /setmainchannel ───────────────────────────────────────────────────────────

async def _set_channel(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]

    if args:
        # Admin passed channel ID directly: /setmainchannel -100123456
        raw = args[0].strip()
        try:
            channel_id = int(raw)
        except ValueError:
            await message.reply(
                "⚠️ Invalid channel ID. Use a numeric ID like <code>-1001234567890</code>\n"
                "Or forward a message from the channel.",
                parse_mode="html",
            )
            return
        await _save_channel(message, channel_id)
    else:
        # Ask them to forward a message
        fsm.set_state(message.from_user.id, fsm.AWAIT_CHANNEL)
        await message.reply(
            "📡 Forward any message from the target channel,\n"
            "or send the channel ID directly (e.g. <code>-1001234567890</code>).\n\n"
            "/cancel to abort.",
            parse_mode="html",
        )


async def _forwarded_channel_handler(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    if fsm.get_state(message.from_user.id) != fsm.AWAIT_CHANNEL:
        return

    # Extract channel ID from forwarded message
    fwd = message.forward_from_chat
    if not fwd:
        await message.reply("⚠️ Could not detect channel from that message.", quote=True)
        return

    await _save_channel(message, fwd.id)


async def _save_channel(message: Message, channel_id: int) -> None:
    await set_main_channel(channel_id)
    fsm.clear(message.from_user.id)
    await message.reply(
        f"✅ Main channel set to <code>{channel_id}</code>.",
        parse_mode="html",
    )


# ── /settings ────────────────────────────────────────────────────────────────

async def _show_settings(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    channel_id = await get_main_channel()
    channel_display = str(channel_id) if channel_id else "Not set"

    text = (
        "<b>⚙️ Bot Settings</b>\n\n"
        f"<b>Main Channel:</b> <code>{channel_display}</code>\n\n"
        "<b>Commands:</b>\n"
        "• /setmainchannel — set post channel\n"
        "• /post &lt;name&gt; — create anime post\n"
        "• /settemplate channel_post — edit channel template\n"
        "• /settemplate bot_message — edit bot message template\n"
        "• /gettemplate channel_post — view template\n"
        "• /cancel — cancel current operation\n"
        "• /skip — skip current quality input"
    )
    await message.reply(text, parse_mode="html")


# ── /settemplate ─────────────────────────────────────────────────────────────

async def _set_template_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    if not args or args[0] not in ("channel_post", "bot_message"):
        await message.reply(
            "Usage: <code>/settemplate channel_post</code> or <code>/settemplate bot_message</code>\n\n"
            "Then send the template text in your next message.",
            parse_mode="html",
        )
        return

    template_name = args[0]
    fsm.set_state(message.from_user.id, fsm.AWAIT_TEMPLATE, {"template_name": template_name})
    await message.reply(
        f"✏️ Send the new template for <b>{template_name}</b>.\n\n"
        "Available variables: <code>{title}</code> <code>{english_title}</code> "
        "<code>{episode}</code> <code>{season}</code> <code>{qualities}</code> "
        "<code>{download_link}</code>\n\n"
        "/cancel to abort.",
        parse_mode="html",
    )


# Intercept template text — handled via a dedicated message filter
# We hook into the text router in post.py group=1 via the AWAIT_TEMPLATE state check below.
# To keep concerns separate, register a separate handler here:

def register(client: Client) -> None:  # noqa: F811 — intentional re-definition to add template msg handler
    client.add_handler(filters.command("setmainchannel") & filters.private, _set_channel)
    client.add_handler(filters.command("settings") & filters.private, _show_settings)
    client.add_handler(filters.command("settemplate") & filters.private, _set_template_cmd)
    client.add_handler(filters.command("gettemplate") & filters.private, _get_template_cmd)
    client.add_handler(filters.forwarded & filters.private, _forwarded_channel_handler, group=2)
    client.add_handler(
        filters.text & filters.private & ~filters.command(["start","cancel","skip",
                                                            "setmainchannel","settemplate",
                                                            "gettemplate","settings","post"]),
        _template_text_handler,
        group=3,
    )


async def _template_text_handler(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return
    if fsm.get_state(uid) != fsm.AWAIT_TEMPLATE:
        return

    data = fsm.get_data(uid)
    template_name = data.get("template_name")
    await set_template(template_name, message.text)
    fsm.clear(uid)
    await message.reply(f"✅ Template <b>{template_name}</b> saved.", parse_mode="html")


# ── /gettemplate ─────────────────────────────────────────────────────────────

async def _get_template_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    name = args[0] if args else "channel_post"
    content = await get_template(name)
    await message.reply(
        f"<b>Template: {escape_html(name)}</b>\n\n"
        f"<code>{escape_html(content)}</code>",
        parse_mode="html",
    )
