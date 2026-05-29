"""
bot/database/crud.py — All database read/write operations.
All data stored in MongoDB Atlas — survives redeployments permanently.
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


async def get_main_channel() -> Optional[int]:
    val = await get_setting("main_channel_id")
    return int(val) if val else None


async def set_main_channel(channel_id: int) -> None:
    await set_setting("main_channel_id", str(channel_id))


# ── Users ─────────────────────────────────────────────────────────────────────

async def save_user(user_id: int, username: str = "", first_name: str = "") -> None:
    """Save user to DB permanently. Upsert so no duplicates."""
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_seen": _now(),
        },
        "$setOnInsert": {"joined_at": _now()}},
        upsert=True,
    )


async def get_all_users() -> list[int]:
    """Return list of all user IDs."""
    cursor = db.users.find({}, {"user_id": 1})
    return [doc["user_id"] async for doc in cursor]


async def get_user_count() -> int:
    return await db.users.count_documents({})


# ── Anime posts ───────────────────────────────────────────────────────────────

async def create_anime_post(data: dict) -> str:
    deep_link_id = nanoid.generate(size=10)
    doc = {**data, "deep_link_id": deep_link_id, "created_at": _now()}
    await db.anime_posts.insert_one(doc)
    return deep_link_id


async def get_post_by_deep_link(deep_link_id: str) -> Optional[dict]:
    return await db.anime_posts.find_one({"deep_link_id": deep_link_id})


# ── Templates ─────────────────────────────────────────────────────────────────

DEFAULT_CHANNEL_TEMPLATE = (
    "<b>{title} • EP{episode}</b>\n"
    "<i>{english_title}</i>\n\n"
    "─────────────────────\n\n"
    "<b>EPISODE</b> • {episode}\n"
    "<b>AUDIO</b> • JAPANESE\n"
    "<b>SUBTITLES</b> • ENGLISH SUBS\n\n"
    "<b>YEAR</b> • {year}\n"
    "<b>GENRES</b> • {genres}\n"
    "<b>RATING</b> • {rating}/100\n\n"
    "─────────────────────\n\n"
    "<b>AVAILABLE QUALITIES</b>\n"
    "{qualities}\n\n"
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
