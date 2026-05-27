"""
bot/utils/admin.py — Admin guard utilities.
"""

import logging
from functools import wraps
from pyrogram.types import Message
from config import config

log = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def admin_only(func):
    """Decorator: silently ignore non-admin callers."""
    @wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.reply("⛔ Admin only.", quote=True)
            return
        return await func(client, message, *args, **kwargs)
    return wrapper
