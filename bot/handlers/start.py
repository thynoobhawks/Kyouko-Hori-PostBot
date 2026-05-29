"""
bot/handlers/start.py — /start handler + user registration.
Every user who starts the bot is saved permanently to MongoDB.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.database.crud import get_post_by_deep_link, save_user, get_user_count
from bot.services.post_builder import send_quality_selection
from bot.utils.admin import is_admin

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(MessageHandler(
        _start_handler,
        filters.command("start") & filters.private,
    ))
    client.add_handler(MessageHandler(
        _users_cmd,
        filters.command("users") & filters.private,
    ))


async def _start_handler(client: Client, message: Message) -> None:
    user = message.from_user

    # Save user permanently to MongoDB
    await save_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
    )

    args = message.command[1:]
    if args:
        await _handle_deep_link(client, message, args[0].strip())
    else:
        await _send_welcome(message)


async def _handle_deep_link(client: Client, message: Message, deep_link_id: str) -> None:
    post = await get_post_by_deep_link(deep_link_id)
    if not post:
        await message.reply("⚠️ This link is invalid or the post was removed.", quote=True)
        return
    await send_quality_selection(client, message.chat.id, post)


async def _send_welcome(message: Message) -> None:
    text = (
        "<b>🎌 Anime Bot</b>\n\n"
        "I post anime episodes to the channel and provide quality download links.\n\n"
        "<i>Click a download button in the channel to get started.</i>"
    )
    await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)


async def _users_cmd(client: Client, message: Message) -> None:
    """Admin command to check total registered users."""
    if not is_admin(message.from_user.id):
        return
    count = await get_user_count()
    await message.reply(
        f"👥 <b>Total Users:</b> <code>{count}</code>",
        parse_mode=enums.ParseMode.HTML,
    )
