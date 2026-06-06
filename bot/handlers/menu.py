"""
bot/handlers/menu.py — Main menu callback handler.
Handles all menu:* callbacks and renders each dashboard screen.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery
from pyrogram.handlers import CallbackQueryHandler

from bot.database.crud import get_main_channel, get_user_count
from bot.ui import messages, keyboards
from bot.utils.admin import is_admin

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(CallbackQueryHandler(
        _menu_router,
        filters.regex(r"^menu:"),
    ))
    client.add_handler(CallbackQueryHandler(
        _settings_router,
        filters.regex(r"^set:"),
    ))
    client.add_handler(CallbackQueryHandler(
        _template_router,
        filters.regex(r"^tpl:"),
    ))
    client.add_handler(CallbackQueryHandler(
        _analytics_router,
        filters.regex(r"^ana:"),
    ))


async def _menu_router(client: Client, query: CallbackQuery) -> None:
    if not is_admin(query.from_user.id):
        await query.answer("admin only", show_alert=True)
        return

    action = query.data.split(":")[1]
    await query.answer()

    if action == "main":
        await query.message.edit_text(
            messages.main_menu(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.main_menu(),
        )

    elif action == "post":
        await query.message.edit_text(
            messages.post_creator(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.post_creator_menu(),
        )

    elif action == "upload":
        await query.message.edit_text(
            messages.post_creator(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.upload_menu(),
        )

    elif action == "channels":
        channel_id = await get_main_channel()
        await query.message.edit_text(
            messages.channel_dashboard(channel_id),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.channel_menu(),
        )

    elif action == "templates":
        await query.message.edit_text(
            messages.template_dashboard(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.template_menu(),
        )

    elif action == "links":
        await query.message.edit_text(
            messages.template_dashboard(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.links_menu(),
        )

    elif action == "settings":
        await query.message.edit_text(
            messages.settings_dashboard(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.settings_menu(),
        )

    elif action == "analytics":
        count = await get_user_count()
        from bot.database.mongo import db
        post_count = await db.anime_posts.count_documents({})
        await query.message.edit_text(
            messages.analytics_dashboard(post_count, count),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.analytics_menu(),
        )


async def _settings_router(client: Client, query: CallbackQuery) -> None:
    if not is_admin(query.from_user.id):
        await query.answer("admin only", show_alert=True)
        return

    await query.answer()
    await query.message.edit_text(
        messages.settings_dashboard(),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.settings_menu(),
    )


async def _template_router(client: Client, query: CallbackQuery) -> None:
    if not is_admin(query.from_user.id):
        await query.answer("admin only", show_alert=True)
        return

    from bot.utils import fsm
    from bot.database.crud import get_template, set_template
    from bot.database.crud import DEFAULT_CHANNEL_TEMPLATE, DEFAULT_BOT_TEMPLATE

    action = query.data.split(":")[1]
    uid = query.from_user.id
    await query.answer()

    if action in ("channel_post", "bot_message"):
        fsm.set_state(uid, fsm.AWAIT_TEMPLATE, {"template_name": action})
        await query.message.edit_text(
            messages.template_prompt(action),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.back_to_main(),
        )

    elif action == "view":
        content = await get_template("channel_post")
        await query.message.edit_text(
            messages.template_view("channel_post", content),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.template_menu(),
        )

    elif action == "reset":
        await set_template("channel_post", DEFAULT_CHANNEL_TEMPLATE)
        await set_template("bot_message", DEFAULT_BOT_TEMPLATE)
        await query.message.edit_text(
            messages.template_saved("all templates"),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.template_menu(),
        )


async def _analytics_router(client: Client, query: CallbackQuery) -> None:
    if not is_admin(query.from_user.id):
        await query.answer("admin only", show_alert=True)
        return

    await query.answer()
    count = await get_user_count()
    from bot.database.mongo import db
    post_count = await db.anime_posts.count_documents({})
    await query.message.edit_text(
        messages.analytics_dashboard(post_count, count),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.analytics_menu(),
    )

