"""
bot/handlers/settings.py — Admin settings commands.
Text handling (template saving) is done in text_router.py.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.database.crud import get_main_channel, get_template
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


async def _set_channel(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    if args:
        try:
            channel_id = int(args[0].strip())
            from bot.database.crud import set_main_channel
            await set_main_channel(channel_id)
            fsm.clear(message.from_user.id)
            await message.reply(
                f"✅ Main channel set to <code>{channel_id}</code>.",
                parse_mode=enums.ParseMode.HTML,
            )
        except ValueError:
            await message.reply(
                "⚠️ Invalid channel ID. Use a numeric ID like <code>-1001234567890</code>",
                parse_mode=enums.ParseMode.HTML,
            )
    else:
        fsm.set_state(message.from_user.id, fsm.AWAIT_CHANNEL)
        await message.reply(
            "📡 Forward any message from the target channel,\n"
            "or send the channel ID (e.g. <code>-1001234567890</code>).\n\n"
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

    from bot.database.crud import set_main_channel
    await set_main_channel(fwd.id)
    fsm.clear(message.from_user.id)
    await message.reply(
        f"✅ Main channel set to <code>{fwd.id}</code>.",
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
        "• /setmainchannel\n"
        "• /post &lt;name&gt;\n"
        "• /settemplate channel_post\n"
        "• /settemplate bot_message\n"
        "• /gettemplate channel_post\n"
        "• /broadcast\n"
        "• /users\n"
        "• /cancel\n"
        "• /skip"
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
        "<b>Variables:</b>\n"
        "<code>{title}</code> <code>{english_title}</code> <code>{episode}</code>\n"
        "<code>{season}</code> <code>{year}</code> <code>{genres}</code>\n"
        "<code>{rating}</code> <code>{total_episodes}</code> <code>{studio}</code>\n"
        "<code>{qualities}</code> <code>{download_link}</code>\n\n"
        "⚠️ Do NOT use <code>{cover_image}</code> — image sent automatically.\n\n"
        "/cancel to abort.",
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

