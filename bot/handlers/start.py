"""
bot/handlers/start.py — /start command handler.

• Plain /start → welcome message
• /start <deep_link_id> → fetch post from DB and show quality buttons
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.database.crud import get_post_by_deep_link
from bot.services.post_builder import send_quality_selection

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(
        # Match /start with or without a payload
        filters.command("start") & filters.private,
        _start_handler,
    )


async def _start_handler(client: Client, message: Message) -> None:
    args = message.command[1:]  # everything after /start

    if args:
        deep_link_id = args[0].strip()
        await _handle_deep_link(client, message, deep_link_id)
    else:
        await _send_welcome(message)


async def _handle_deep_link(client: Client, message: Message, deep_link_id: str) -> None:
    post = await get_post_by_deep_link(deep_link_id)
    if not post:
        await message.reply(
            "⚠️ This link is invalid or the post was removed.",
            quote=True,
        )
        return

    await send_quality_selection(client, message.chat.id, post)


async def _send_welcome(message: Message) -> None:
    text = (
        "<b>🎌 Anime Bot</b>\n\n"
        "I post anime episodes to the channel and provide quality download links.\n\n"
        "<i>Click a download button in the channel to get started.</i>"
    )
    await message.reply(text, parse_mode="html", disable_web_page_preview=True)
