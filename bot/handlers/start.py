"""
bot/handlers/start.py — /start handler with new UI.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.database.crud import get_post_by_deep_link, save_user, get_user_count
from bot.services.post_builder import send_quality_selection
from bot.utils.admin import is_admin
from bot.ui import messages, keyboards, theme

log = logging.getLogger(__name__)

# Replace with your actual Hori image URL
WELCOME_IMAGE = "https://files.catbox.moe/your-hori-image.jpg"


def register(client: Client) -> None:
    client.add_handler(MessageHandler(_start_handler, filters.command("start") & filters.private))
    client.add_handler(MessageHandler(_users_cmd, filters.command("users") & filters.private))
    client.add_handler(MessageHandler(_menu_cmd, filters.command("menu") & filters.private))


async def _start_handler(client: Client, message: Message) -> None:
    user = message.from_user
    await save_user(user_id=user.id, username=user.username or "", first_name=user.first_name or "")

    args = message.command[1:]
    if args:
        await _handle_deep_link(client, message, args[0].strip())
        return

    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=WELCOME_IMAGE,
            caption=messages.welcome(user.first_name or "there"),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.main_menu(),
        )
    except Exception:
        # Fallback if image fails
        await message.reply(
            messages.welcome(user.first_name or "there"),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.main_menu(),
        )


async def _handle_deep_link(client: Client, message: Message, deep_link_id: str) -> None:
    post = await get_post_by_deep_link(deep_link_id)
    if not post:
        await message.reply(
            messages.error("this link is invalid or the post was removed"),
            parse_mode=enums.ParseMode.HTML,
        )
        return
    await send_quality_selection(client, message.chat.id, post)


async def _menu_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.reply(
        messages.main_menu(),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.main_menu(),
    )


async def _users_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    count = await get_user_count()
    from bot.ui.theme import sc, bold, bullet
    await message.reply(
        f"{bold(sc('users'))}\n\n{bullet(sc('total registered'))} · {bold(str(count))}",
        parse_mode=enums.ParseMode.HTML,
    )
