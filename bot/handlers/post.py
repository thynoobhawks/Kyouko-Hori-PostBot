"""
bot/handlers/post.py — /post, /skip, /cancel with new UI.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.services.anilist import fetch_anime
from bot.utils.admin import is_admin
from bot.utils import fsm
from bot.database.crud import get_main_channel
from bot.ui import messages, keyboards

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(MessageHandler(_post_command, filters.command("post") & filters.private))
    client.add_handler(MessageHandler(_cancel_command, filters.command("cancel") & filters.private))
    client.add_handler(MessageHandler(_skip_command, filters.command("skip") & filters.private))


async def _post_command(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    channel = await get_main_channel()
    if not channel:
        await message.reply(
            messages.no_channel(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.channel_menu(),
        )
        return

    args = message.command[1:]
    if not args:
        await message.reply(
            messages.post_creator(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.post_creator_menu(),
        )
        return

    raw_query = " ".join(args)
    uid = message.from_user.id
    fsm.clear(uid)

    status_msg = await message.reply(
        messages.post_fetching(raw_query),
        parse_mode=enums.ParseMode.HTML,
    )

    anime = await fetch_anime(raw_query)
    if not anime:
        await status_msg.edit_text(
            messages.post_not_found(raw_query),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.back_to_main(),
        )
        return

    episode_hint = anime.pop("_episode_hint", args[-1])

    fsm.set_state(uid, fsm.AWAIT_MEDIA, {
        "anime_info": anime,
        "episode": episode_hint,
        "qualities": {},
        "custom_media": None,
        "custom_media_type": None,
    })

    await status_msg.edit_text(
        messages.post_found(anime, episode_hint),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )
    await message.reply(
        messages.post_custom_media(),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.skip_cancel_row(),
    )


async def _skip_command(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return

    state = fsm.get_state(uid)

    if state == fsm.AWAIT_MEDIA:
        fsm.set_state(uid, fsm.AWAIT_480P)
        await message.reply(
            messages.post_quality_prompt("480p"),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.skip_cancel_row(),
        )
        return

    if state not in fsm.QUALITY_STATES:
        await message.reply(
            messages.nothing_to_skip(),
            parse_mode=enums.ParseMode.HTML,
        )
        return

    label = fsm.quality_label_for_state(state)
    next_state = fsm.NEXT_QUALITY_STATE[state]

    if next_state == fsm.AWAIT_CONFIRM:
        fsm.set_state(uid, fsm.AWAIT_CONFIRM)
        from bot.handlers.text_router import _send_preview
        await _send_preview(message, uid)
    else:
        fsm.set_state(uid, next_state)
        next_label = fsm.quality_label_for_state(next_state)
        await message.reply(
            messages.post_skipped(label, next_label),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.skip_cancel_row(),
        )


async def _cancel_command(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return
    fsm.clear(uid)
    await message.reply(
        messages.post_cancelled(),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.back_to_main(),
    )

