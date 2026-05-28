"""
bot/handlers/settings.py — Admin settings commands.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.database.crud import set_main_channel, get_main_channel, get_template, set_template
from bot.utils.admin import is_admin
from bot.utils.html import escape_html
from bot.utils import fsm

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(MessageHandler(_set_channel, filters.command("setmainchannel") & filters.private))
    client.add_handler(MessageHandler(_show_settings, filters.command("settings") & filters.private))
    client.add_handler(MessageHandler(_set_template_cmd, filters.command("settemplate") & filters.private))
    client.add_handler(MessageHandler(_get_template_cmd, filters.command("gettemplate") & filters.private))
    client.add_handler(MessageHandler(_forwarded_channel_handler, filters.forwarded & filters.private))
    client.add_handler(MessageHandler(
        _template_text_handler,
        filters.text & filters.private & ~filters.command([
            "start", "cancel", "skip", "setmainchannel",
            "settemplate", "gettemplate", "settings", "post"
        ]),
    ))


async def _set_channel(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    if args:
        try:
            channel_id = int(args[0].strip())
        except ValueError:
            await message.reply(
                "⚠️ Invalid channel ID. Use a numeric ID like <code>-1001234567890</code>\n"
                "Or forward a message from the channel.",
                parse_mode=enums.ParseMode.HTML,
            )
            return
        await _save_channel(message, channel_id)
    else:
        fsm.set_state(message.from_user.id, fsm.AWAIT_CHANNEL)
        await message.reply(
            "📡 Forward any message from the target channel,\n"
            "or send the channel ID directly (e.g. <code>-1001234567890</code>).\n\n"
            "/cancel to abort.",
            parse_mode=enums.ParseMode.HTML,
        )


async def _forwarded_channel_handler(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    if fsm.get_state(message.from_user.id) != fsm.AWAIT_CHANNEL:
        return

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
        parse_mode=enums.ParseMode.HTML,
    )


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
        "• /settemplate channel_post\n"
        "• /settemplate bot_message\n"
        "• /gettemplate channel_post\n"
        "• /cancel — cancel current operation\n"
        "• /skip — skip current quality input"
    )
    await message.reply(text, parse_mode=enums.ParseMode.HTML)


async def _set_template_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    if not args or args[0] not in ("channel_post", "bot_message"):
        await message.reply(
            "Usage: <code>/settemplate channel_post</code> or <code>/settemplate bot_message</code>",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    template_name = args[0]
    fsm.set_state(message.from_user.id, fsm.AWAIT_TEMPLATE, {"template_name": template_name})
    await message.reply(
        f"✏️ Send the new template for <b>{template_name}</b>.\n\n"
        "Variables: <code>{title}</code> <code>{english_title}</code> "
        "<code>{episode}</code> <code>{season}</code> <code>{qualities}</code> "
        "<code>{download_link}</code>\n\n/cancel to abort.",
        parse_mode=enums.ParseMode.HTML,
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
    await message.reply(
        f"✅ Template <b>{template_name}</b> saved.",
        parse_mode=enums.ParseMode.HTML,
    )


async def _get_template_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    name = args[0] if args else "channel_post"
    content = await get_template(name)
    await message.reply(
        f"<b>Template: {escape_html(name)}</b>\n\n<code>{escape_html(content)}</code>",
        parse_mode=enums.ParseMode.HTML,
    )

