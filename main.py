"""
bot/handlers/start.py — /start command handler.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.database.crud import get_post_by_deep_link
from bot.services.post_builder import send_quality_selection

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(MessageHandler(
        _start_handler,
        filters.command("start") & filters.private,
    ))


async def _start_handler(client: Client, message: Message) -> None:
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
