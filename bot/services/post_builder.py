"""
bot/services/post_builder.py — Builds and publishes formatted anime posts.
"""

import logging
from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.crud import get_template, get_main_channel, create_anime_post
from bot.utils.html import escape_html
from config import config

log = logging.getLogger(__name__)


async def build_and_post(client: Client, session: dict) -> str | None:
    anime = session["anime_info"]
    episode = session.get("episode", "?")
    qualities: dict[str, str] = session.get("qualities", {})

    quality_list_text = "\n".join(f"• {q}" for q in qualities.keys()) if qualities else "• N/A"

    post_data = {
        "title": anime["title_romaji"],
        "english_title": anime["title_english"],
        "anilist_id": anime["anilist_id"],
        "cover_image": anime["cover_image"],
        "synopsis": anime["synopsis"],
        "genres": anime["genres"],
        "status": anime["status"],
        "season": anime["season"],
        "season_year": anime["season_year"],
        "total_episodes": anime["total_episodes"],
        "rating": anime["rating"],
        "episode": episode,
        "qualities": qualities,
    }

    deep_link_id = await create_anime_post(post_data)
    bot_link = f"https://t.me/{config.BOT_USERNAME}?start={deep_link_id}"

    template = await get_template("channel_post")
    text = template.format(
        title=escape_html(anime["title_romaji"]),
        english_title=escape_html(anime["title_english"]),
        episode=escape_html(str(episode)),
        season=escape_html(str(anime["season"])),
        qualities=escape_html(quality_list_text),
        subtitles="ENGLISH SUBS",
        audio="JAPANESE",
        download_link=bot_link,
    )

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ", url=bot_link)]]
    )

    channel_id = await get_main_channel()
    if not channel_id:
        log.error("Main channel not configured — cannot post.")
        return None

    try:
        if anime.get("cover_image"):
            await client.send_photo(
                chat_id=channel_id,
                photo=anime["cover_image"],
                caption=text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=markup,
            )
        else:
            await client.send_message(
                chat_id=channel_id,
                text=text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=markup,
                disable_web_page_preview=True,
            )
        log.info(f"Posted '{anime['title_romaji']}' ep {episode} → channel {channel_id}")
    except Exception as e:
        log.error(f"Failed to send channel post: {e}")
        return None

    return deep_link_id


async def send_quality_selection(client: Client, chat_id: int, post: dict) -> None:
    qualities: dict = post.get("qualities", {})

    template = await get_template("bot_message")
    quality_list = ", ".join(qualities.keys()) if qualities else "N/A"

    text = template.format(
        title=escape_html(post.get("title", "Unknown")),
        episode=escape_html(str(post.get("episode", "?"))),
        qualities=escape_html(quality_list),
    )

    buttons = [[InlineKeyboardButton(f"📥 {label.upper()}", url=url)] for label, url in qualities.items()]
    markup = InlineKeyboardMarkup(buttons) if buttons else None

    cover = post.get("cover_image")
    try:
        if cover:
            await client.send_photo(
                chat_id=chat_id,
                photo=cover,
                caption=text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=markup,
            )
        else:
            await client.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=markup,
                disable_web_page_preview=True,
            )
    except Exception as e:
        log.error(f"Failed to send quality selection to {chat_id}: {e}")

