"""
bot/database/crud.py — All database read/write operations.
"""

from datetime import datetime, timezone
from typing import Optional
import nanoid

from bot.database.mongo import db


async def get_setting(key: str) -> Optional[str]:
    doc = await db.settings.find_one({"key": key})
    return doc["value"] if doc else None


async def set_setting(key: str, value) -> None:
    await db.settings.update_one(
        {"key": key},
        {"$set": {"key": key, "value": value, "updated_at": _now()}},
        upsert=True,
    )


async def get_main_channel() -> Optional[int]:
    val = await get_setting("main_channel_id")
    return int(val) if val else None


async def set_main_channel(channel_id: int) -> None:
    await set_setting("main_channel_id", str(channel_id))


async def create_anime_post(data: dict) -> str:
    deep_link_id = nanoid.generate(size=10)
    doc = {**data, "deep_link_id": deep_link_id, "created_at": _now()}
    await db.anime_posts.insert_one(doc)
    return deep_link_id


async def get_post_by_deep_link(deep_link_id: str) -> Optional[dict]:
    return await db.anime_posts.find_one({"deep_link_id": deep_link_id})


# ── Templates ─────────────────────────────────────────────────────────────────
# Note: No &#8205; trick needed — cover image is sent as actual photo
# Caption is used for channel posts and bot messages

DEFAULT_CHANNEL_TEMPLATE = (
    "<b>{title} • EP{episode}</b>\n"
    "<i>{english_title}</i>\n\n"
    "─────────────────────\n"
    "<blockquote expandable>"
    "<b>EPISODE</b> • {episode}\n"
    "<b>AUDIO</b> • JAPANESE\n"
    "<b>SUBTITLES</b> • ENGLISH SUBS\n\n"
    "<b>YEAR</b> • {year}\n"
    "<b>GENRES</b> • {genres}\n"
    "<b>RATING</b> • {rating}/100\n\n"
    "─────────────────────\n\n"
    "<b>AVAILABLE QUALITIES</b>\n"
    "{qualities}\n"
    "</blockquote>\n"
    "<a href=\"{download_link}\">ᴅᴏᴡɴʟᴏᴀᴅ ᴇᴘɪꜱᴏᴅᴇ</a>"
)

DEFAULT_BOT_TEMPLATE = (
    "<b>{title}</b>\n"
    "<i>{english_title}</i>\n\n"
    "<b>EPISODE</b> • {episode}\n"
    "<b>YEAR</b> • {year}\n"
    "<b>GENRES</b> • {genres}\n"
    "<b>RATING</b> • {rating}/100\n\n"
    "<i>Select preferred quality below.</i>"
)


async def get_template(name: str) -> str:
    doc = await db.templates.find_one({"name": name})
    if doc:
        return doc["content"]
    defaults = {
        "channel_post": DEFAULT_CHANNEL_TEMPLATE,
        "bot_message": DEFAULT_BOT_TEMPLATE,
    }
    return defaults.get(name, "")


async def set_template(name: str, content: str) -> None:
    await db.templates.update_one(
        {"name": name},
        {"$set": {"name": name, "content": content, "updated_at": _now()}},
        upsert=True,
    )


def _now():
    return datetime.now(timezone.utc)
