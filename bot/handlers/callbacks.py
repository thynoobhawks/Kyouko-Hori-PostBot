"""
bot/handlers/callbacks.py — Inline keyboard callback query handler.
"""

import logging
from pyrogram import Client, enums
from pyrogram.types import CallbackQuery
from pyrogram.handlers import CallbackQueryHandler

from bot.services.post_builder import build_and_post
from bot.utils.admin import is_admin
from bot.utils import fsm
from config import config

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(CallbackQueryHandler(
        _post_callback,
        lambda _, __, query: query.data.startswith(("confirm_post:", "cancel_post:")),
    ))


async def _post_callback(client: Client, query: CallbackQuery) -> None:
    uid = query.from_user.id
    if not is_admin(uid):
        await query.answer("⛔ Admins only.", show_alert=True)
        return

    action, owner_uid_str = query.data.split(":", 1)
    owner_uid = int(owner_uid_str)

    if uid != owner_uid:
        await query.answer("⛔ Not your session.", show_alert=True)
        return

    if action == "cancel_post":
        fsm.clear(uid)
        await query.message.edit_text("🚫 Post cancelled.")
        await query.answer("Cancelled.")
        return

    state = fsm.get_state(uid)
    if state != fsm.AWAIT_CONFIRM:
        await query.answer("⚠️ Session expired. Start over with /post.", show_alert=True)
        return

    data = fsm.get_data(uid)
    await query.message.edit_text("⏳ Posting to channel…")

    deep_link_id = await build_and_post(client, data)
    fsm.clear(uid)

    if deep_link_id:
        bot_link = f"https://t.me/{config.BOT_USERNAME}?start={deep_link_id}"
        await query.message.edit_text(
            f"✅ <b>Posted!</b>\n\nDeep link: <code>{bot_link}</code>",
            parse_mode=enums.ParseMode.HTML,
        )
    else:
        await query.message.edit_text("❌ Failed to post. Check bot channel permissions and logs.")

    await query.answer()
