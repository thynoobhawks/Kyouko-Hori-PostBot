"""
bot/handlers/post.py — /post command + multi-step quality link collection.

Flow:
  /post <anime name + episode>
    → fetch AniList
    → ask for 480p link  (skippable with /skip)
    → ask for 720p link
    → ask for 1080p link
    → ask for 4K link
    → preview
    → confirm → publish to channel
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler

from bot.services.anilist import fetch_anime
from bot.services.post_builder import build_and_post
from bot.utils.admin import is_admin
from bot.utils.html import escape_html, SEPARATOR
from bot.utils import fsm
from bot.database.crud import get_main_channel
from config import config

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    # /post command
    client.add_handler(MessageHandler(
        _post_command,
        filters.command("post") & filters.private,
    ))
    # /cancel
    client.add_handler(MessageHandler(
        _cancel_command,
        filters.command("cancel") & filters.private,
    ))
    # /skip
    client.add_handler(MessageHandler(
        _skip_command,
        filters.command("skip") & filters.private,
    ))
    # Text messages during a post session
    client.add_handler(MessageHandler(
        _text_router,
        filters.text & filters.private & ~filters.command([
            "start", "cancel", "skip", "setmainchannel",
            "settemplate", "gettemplate", "settings", "post"
        ]),
    ))


# ── /post ─────────────────────────────────────────────────────────────────────

async def _post_command(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    channel = await get_main_channel()
    if not channel:
        await message.reply(
            "⚠️ No main channel set. Use /setmainchannel first.",
            quote=True,
        )
        return

    args = message.command[1:]
    if not args:
        await message.reply(
            "Usage: <code>/post Anime Name Episode Number</code>\n"
            "Example: <code>/post Dandadan Episode 08</code>",
            parse_mode="html",
            quote=True,
        )
        return

    search_query = " ".join(args)
    uid = message.from_user.id
    fsm.clear(uid)

    status_msg = await message.reply("🔍 Fetching anime info from AniList…", quote=True)

    anime = await fetch_anime(search_query)
    if not anime:
        await status_msg.edit_text(
            f"❌ Could not find anime for: <b>{escape_html(search_query)}</b>\n"
            "Try a more precise title.",
            parse_mode="html",
        )
        return

    episode_hint = _extract_episode(args)

    fsm.set_state(uid, fsm.AWAIT_480P, {
        "anime_info": anime,
        "episode": episode_hint,
        "qualities": {},
    })

    await status_msg.edit_text(
        _anime_preview_text(anime, episode_hint),
        parse_mode="html",
        disable_web_page_preview=True,
    )

    await message.reply(
        "📎 Send the <b>480p</b> download link.\n"
        "Or /skip to skip this quality. /cancel to abort.",
        parse_mode="html",
    )


# ── Text router (FSM steps) ────────────────────────────────────────────────────

async def _text_router(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return

    state = fsm.get_state(uid)
    if state not in fsm.QUALITY_STATES:
        return

    link = message.text.strip()

    if not (link.startswith("http://") or link.startswith("https://") or link.startswith("tg://")):
        await message.reply(
            "⚠️ That doesn't look like a valid URL. Send a link or /skip.",
            quote=True,
        )
        return

    label = fsm.quality_label_for_state(state)
    data = fsm.get_data(uid)
    data["qualities"][label] = link

    next_state = fsm.NEXT_QUALITY_STATE[state]

    if next_state == fsm.AWAIT_CONFIRM:
        fsm.set_state(uid, fsm.AWAIT_CONFIRM, data)
        await _send_preview(client, message, uid)
    else:
        fsm.set_state(uid, next_state, data)
        next_label = fsm.quality_label_for_state(next_state)
        await message.reply(
            f"✅ Saved {label}.\n\n"
            f"📎 Send the <b>{next_label.upper()}</b> link, /skip, or /cancel.",
            parse_mode="html",
            quote=True,
        )


# ── /skip ─────────────────────────────────────────────────────────────────────

async def _skip_command(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return

    state = fsm.get_state(uid)
    if state not in fsm.QUALITY_STATES:
        await message.reply("Nothing to skip right now.", quote=True)
        return

    label = fsm.quality_label_for_state(state)
    next_state = fsm.NEXT_QUALITY_STATE[state]

    if next_state == fsm.AWAIT_CONFIRM:
        fsm.set_state(uid, fsm.AWAIT_CONFIRM)
        await message.reply(f"⏭ Skipped {label}.", quote=True)
        await _send_preview(client, message, uid)
    else:
        fsm.set_state(uid, next_state)
        next_label = fsm.quality_label_for_state(next_state)
        await message.reply(
            f"⏭ Skipped {label}.\n\n"
            f"📎 Send the <b>{next_label.upper()}</b> link, /skip, or /cancel.",
            parse_mode="html",
            quote=True,
        )


# ── /cancel ───────────────────────────────────────────────────────────────────

async def _cancel_command(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not is_admin(uid):
        return
    fsm.clear(uid)
    await message.reply("🚫 Post creation cancelled.", quote=True)


# ── Preview + Confirm ─────────────────────────────────────────────────────────

async def _send_preview(client: Client, message: Message, uid: int) -> None:
    data = fsm.get_data(uid)
    anime = data["anime_info"]
    qualities = data.get("qualities", {})
    episode = data.get("episode", "?")

    quality_text = "\n".join(f"  • {k}" for k in qualities.keys()) if qualities else "  • (none)"

    preview = (
        f"<b>📋 Preview</b>\n{SEPARATOR}\n\n"
        f"<b>{escape_html(anime['title_romaji'])}</b>\n"
        f"<i>{escape_html(anime['title_english'])}</i>\n\n"
        f"<b>Episode:</b> {escape_html(str(episode))}\n"
        f"<b>Season:</b> {escape_html(str(anime['season']))}\n\n"
        f"<b>Qualities:</b>\n{escape_html(quality_text)}\n\n"
        f"{SEPARATOR}\n"
        f"<i>Confirm to post to channel?</i>"
    )

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Post Now", callback_data=f"confirm_post:{uid}"),
            InlineKeyboardButton("❌ Cancel",   callback_data=f"cancel_post:{uid}"),
        ]
    ])

    await message.reply(preview, parse_mode="html", reply_markup=markup, quote=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_episode(args: list[str]) -> str:
    for token in reversed(args):
        if token.isdigit():
            return token
        if token.lower().startswith("episode"):
            return token
    return " ".join(args[-2:]) if len(args) >= 2 else args[-1]


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

