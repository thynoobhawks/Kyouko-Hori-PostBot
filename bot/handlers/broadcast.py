"""
bot/handlers/broadcast.py — Broadcast system with new UI.
"""

import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.database.crud import get_all_users
from bot.utils.admin import is_admin
from bot.utils import fsm
from bot.ui import messages, keyboards

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(MessageHandler(_broadcast_cmd, filters.command("broadcast") & filters.private))
    client.add_handler(MessageHandler(_cancelbroadcast_cmd, filters.command("cancelbroadcast") & filters.private))
    client.add_handler(MessageHandler(
        _media_handler,
        filters.private & (filters.photo | filters.video),
    ))


async def _broadcast_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    fsm.set_state(message.from_user.id, fsm.AWAIT_BROADCAST)
    await message.reply(
        messages.broadcast_prompt(),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.back_to_main(),
    )


async def _cancelbroadcast_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    fsm.clear(message.from_user.id)
    await message.reply(
        messages.post_cancelled(),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.back_to_main(),
    )


async def _media_handler(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return

    state = fsm.get_state(uid)

    if state == fsm.AWAIT_BROADCAST:
        await _do_broadcast(client, message, uid)

    elif state == fsm.AWAIT_MEDIA:
        if message.photo:
            file_id, media_type = message.photo.file_id, "photo"
        elif message.video:
            file_id, media_type = message.video.file_id, "video"
        else:
            return

        fsm.update_data(uid, custom_media=file_id, custom_media_type=media_type)
        fsm.set_state(uid, fsm.AWAIT_480P)
        await message.reply(
            messages.post_quality_prompt("480p"),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.skip_cancel_row(),
            quote=True,
        )


async def _do_broadcast(client: Client, message: Message, uid: int) -> None:
    fsm.clear(uid)
    users = await get_all_users()
    if not users:
        await message.reply(messages.error("no users found in database"), parse_mode=enums.ParseMode.HTML)
        return

    status_msg = await message.reply(
        messages.broadcast_sending(len(users)),
        parse_mode=enums.ParseMode.HTML,
    )

    success = failed = 0
    for user_id in users:
        try:
            if message.photo:
                await client.send_photo(chat_id=user_id, photo=message.photo.file_id,
                                        caption=message.caption or "", parse_mode=enums.ParseMode.HTML)
            elif message.video:
                await client.send_video(chat_id=user_id, video=message.video.file_id,
                                        caption=message.caption or "", parse_mode=enums.ParseMode.HTML)
            else:
                await client.send_message(chat_id=user_id, text=message.text,
                                          parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
            success += 1
        except Exception as e:
            log.warning(f"Broadcast failed for {user_id}: {e}")
            failed += 1
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        messages.broadcast_done(success, failed),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.back_to_main(),
    )

