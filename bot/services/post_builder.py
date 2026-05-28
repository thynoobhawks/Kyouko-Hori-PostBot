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
    genres_text = ", ".join(anime.get("genres", [])[:5]) or "N/A"
    year_text = str(anime.get("season_year", "")) or "N/A"
    cover_image = anime.get("cover_image", "")

    post_data = {
        "title": anime["title_romaji"],
        "english_title": anime["title_english"],
        "anilist_id": anime["anilist_id"],
        "cover_image": cover_image,
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
        year=escape_html(year_text),
        genres=escape_html(genres_text),
        rating=escape_html(str(anime["rating"])),
        total_episodes=escape_html(str(anime["total_episodes"])),
        studio=escape_html(anime.get("studio", "N/A")),
        qualities=escape_html(quality_list_text),
        subtitles="ENGLISH SUBS",
        audio="JAPANESE",
        cover_image=cover_image,
        download_link=bot_link,
    )

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ", url=bot_link)]]
    )

    channel_id = await get_main_channel()
    if not channel_id:
        log.error("Main channel not configured.")
        return None

    try:
        # Send as text with link preview (cover_image embedded in template as hidden link)
        # This gives the rich preview card effect
        await client.send_message(
            chat_id=channel_id,
            text=text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=markup,
            disable_web_page_preview=False,  # MUST be False for preview to show
        )
        log.info(f"Posted '{anime['title_romaji']}' ep {episode} → channel {channel_id}")
    except Exception as e:
        log.error(f"Failed to send channel post: {e}")
        return None

    return deep_link_id


async def send_quality_selection(client: Client, chat_id: int, post: dict) -> None:
    """Bot-side quality selection shown when user opens deep link."""
    qualities: dict = post.get("qualities", {})
    cover_image = post.get("cover_image", "")

    template = await get_template("bot_message")
    quality_list = ", ".join(qualities.keys()) if qualities else "N/A"
    genres_text = ", ".join(post.get("genres", [])[:5]) or "N/A"
    year_text = str(post.get("season_year", "")) or "N/A"

    text = template.format(
        title=escape_html(post.get("title", "Unknown")),
        english_title=escape_html(post.get("english_title", "")),
        episode=escape_html(str(post.get("episode", "?"))),
        qualities=escape_html(quality_list),
        genres=escape_html(genres_text),
        year=escape_html(year_text),
        rating=escape_html(str(post.get("rating", "N/A"))),
        total_episodes=escape_html(str(post.get("total_episodes", "?"))),
        studio=escape_html(post.get("studio", "N/A")),
        cover_image=cover_image,
        season=escape_html(str(post.get("season", "?"))),
    )

    buttons = [
        [InlineKeyboardButton(f"📥 {label.upper()}", url=url)]
        for label, url in qualities.items()
    ]
    markup = InlineKeyboardMarkup(buttons) if buttons else None

    try:
        await client.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=markup,
            disable_web_page_preview=False,  # show cover preview
        )
    except Exception as e:
        log.error(f"Failed to send quality selection to {chat_id}: {e}")

