"""
bot/handlers/post.py — /post, /skip, /cancel commands only.
Text/media routing handled by text_router.py and broadcast.py.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.services.anilist import fetch_anime
from bot.utils.admin import is_admin
from bot.utils.html import escape_html
from bot.utils import fsm
from bot.database.crud import get_main_channel

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
        await message.reply("⚠️ No main channel set. Use /setmainchannel first.", quote=True)
        return

    args = message.command[1:]
    if not args:
        await message.reply(
            "Usage: <code>/post Anime Name Episode Number</code>\n"
            "Example: <code>/post Dandadan Episode 08</code>",
            parse_mode=enums.ParseMode.HTML,
            quote=True,
        )
        return

    raw_query = " ".join(args)
    uid = message.from_user.id
    fsm.clear(uid)

    status_msg = await message.reply("🔍 Fetching anime info from AniList…", quote=True)

    anime = await fetch_anime(raw_query)
    if not anime:
        await status_msg.edit_text(
            f"❌ Could not find: <b>{escape_html(raw_query)}</b>\n\n"
            "Tips:\n• Use exact anime title\n• Try English or Romaji\n• Remove episode number",
            parse_mode=enums.ParseMode.HTML,
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
        _anime_preview_text(anime, episode_hint),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )
    await message.reply(
        "🖼 <b>Custom Poster (Optional)</b>\n\n"
        "Send a <b>photo</b> or <b>video</b> to use as post media.\n"
        "Or /skip to use auto-generated card.",
        parse_mode=enums.ParseMode.HTML,
    )


async def _skip_command(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return

    state = fsm.get_state(uid)

    if state == fsm.AWAIT_MEDIA:
        fsm.set_state(uid, fsm.AWAIT_480P)
        await message.reply(
            "⏭ Using auto-generated card.\n\n"
            "📎 Send the <b>480p</b> download link.\nOr /skip. /cancel to abort.",
            parse_mode=enums.ParseMode.HTML,
            quote=True,
        )
        return

    if state not in fsm.QUALITY_STATES:
        await message.reply("Nothing to skip right now.", quote=True)
        return

    label = fsm.quality_label_for_state(state)
    next_state = fsm.NEXT_QUALITY_STATE[state]

    if next_state == fsm.AWAIT_CONFIRM:
        fsm.set_state(uid, fsm.AWAIT_CONFIRM)
        await message.reply(f"⏭ Skipped {label}.", quote=True)
        # Trigger preview via text_router
        from bot.handlers.text_router import _send_preview
        await _send_preview(message, uid)
    else:
        fsm.set_state(uid, next_state)
        next_label = fsm.quality_label_for_state(next_state)
        await message.reply(
            f"⏭ Skipped {label}.\n\n"
            f"📎 Send the <b>{next_label.upper()}</b> link, /skip, or /cancel.",
            parse_mode=enums.ParseMode.HTML,
            quote=True,
        )


async def _cancel_command(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return
    fsm.clear(uid)
    await message.reply("🚫 Post creation cancelled.", quote=True)


def _anime_preview_text(anime: dict, episode: str) -> str:
    genres = ", ".join(anime.get("genres", [])[:4]) or "N/A"
    return (
        f"<b>✅ Found: {escape_html(anime['title_romaji'])}</b>\n"
        f"<i>{escape_html(anime['title_english'])}</i>\n\n"
        f"<b>Episode:</b> {escape_html(str(episode))}\n"
        f"<b>Season:</b> {escape_html(str(anime['season']))} {anime.get('season_year','')}\n"
        f"<b>Episodes:</b> {anime['total_episodes']}\n"
        f"<b>Rating:</b> {anime['rating']}/100\n"
        f"<b>Genres:</b> {escape_html(genres)}\n\n"
        f"<i>{escape_html(anime['synopsis'])}</i>"
    )

