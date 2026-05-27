"""
bot/database/crud.py — All database read/write operations.
Keeps handlers clean by abstracting every DB call here.
"""

from datetime import datetime, timezone
from typing import Optional
import nanoid

from bot.database.mongo import db


# ── Settings ──────────────────────────────────────────────────────────────────

async def get_setting(key: str) -> Optional[str]:
    doc = await db.settings.find_one({"key": key})
    return doc["value"] if doc else None


async def set_setting(key: str, value) -> None:
    await db.settings.update_one(
        {"key": key},
        {"$set": {"key": key, "value": value, "updated_at": _now()}},
        upsert=True,
    )


# ── Main channel ──────────────────────────────────────────────────────────────

async def get_main_channel() -> Optional[int]:
    val = await get_setting("main_channel_id")
    return int(val) if val else None


async def set_main_channel(channel_id: int) -> None:
    await set_setting("main_channel_id", str(channel_id))


# ── Anime posts ───────────────────────────────────────────────────────────────

async def create_anime_post(data: dict) -> str:
    """
    Insert a new anime post document.
    Returns the generated deep_link_id (short unique string).
    """
    deep_link_id = nanoid.generate(size=10)
    doc = {
        **data,
        "deep_link_id": deep_link_id,
        "created_at": _now(),
    }
    await db.anime_posts.insert_one(doc)
    return deep_link_id


async def get_post_by_deep_link(deep_link_id: str) -> Optional[dict]:
    return await db.anime_posts.find_one({"deep_link_id": deep_link_id})


async def get_post_by_id(post_id: str) -> Optional[dict]:
    from bson import ObjectId
    return await db.anime_posts.find_one({"_id": ObjectId(post_id)})


# ── Templates ─────────────────────────────────────────────────────────────────

DEFAULT_CHANNEL_TEMPLATE = (
    "<b>{title} • S{season}</b>\n"
    "<i>{english_title}</i>\n\n"
    "─────────────────────\n\n"
    "<blockquote expandable>"
    "<b>EPISODE</b>\n• {episode}\n\n"
    "<b>AUDIO</b>\n• JAPANESE\n\n"
    "─────────────────────\n\n"
    "<b>AVAILABLE QUALITIES</b>\n• {qualities}\n\n"
    "─────────────────────\n\n"
    "<b>SUBTITLES</b>\n• ENGLISH SUBS\n"
    "</blockquote>"
    '<a href="{download_link}">ᴅᴏᴡɴʟᴏᴀᴅ ᴇᴘɪꜱᴏᴅᴇ</a>'
)

DEFAULT_BOT_TEMPLATE = (
    "<b>{title}</b>\n\n"
    "<blockquote>\n"
    "• EPISODE : {episode}\n"
    "• AVAILABLE : {qualities}\n"
    "</blockquote>\n"
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc)
