"""
bot/handlers/settings.py — Settings commands with new UI.
"""

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from bot.database.crud import get_main_channel, get_template
from bot.utils.admin import is_admin
from bot.utils import fsm
from bot.ui import messages, keyboards

log = logging.getLogger(__name__)


def register(client: Client) -> None:
    client.add_handler(MessageHandler(_set_channel, filters.command("setmainchannel") & filters.private))
    client.add_handler(MessageHandler(_show_settings, filters.command("settings") & filters.private))
    client.add_handler(MessageHandler(_set_template_cmd, filters.command("settemplate") & filters.private))
    client.add_handler(MessageHandler(_get_template_cmd, filters.command("gettemplate") & filters.private))
    client.add_handler(MessageHandler(_forwarded_channel_handler, filters.forwarded & filters.private))


async def _set_channel(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    if args:
        try:
            channel_id = int(args[0].strip())
            from bot.database.crud import set_main_channel
            await set_main_channel(channel_id)
            fsm.clear(message.from_user.id)
            await message.reply(
                messages.channel_saved(channel_id),
                parse_mode=enums.ParseMode.HTML,
                reply_markup=keyboards.channel_menu(),
            )
        except ValueError:
            await message.reply(
                messages.error("invalid channel id format"),
                parse_mode=enums.ParseMode.HTML,
            )
    else:
        fsm.set_state(message.from_user.id, fsm.AWAIT_CHANNEL)
        await message.reply(
            messages.channel_set_prompt(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboards.back_to_main(),
        )


async def _forwarded_channel_handler(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    if fsm.get_state(message.from_user.id) != fsm.AWAIT_CHANNEL:
        return

    fwd = message.forward_from_chat
    if not fwd:
        await message.reply(messages.error("could not detect channel from that message"), quote=True)
        return

    from bot.database.crud import set_main_channel
    await set_main_channel(fwd.id)
    fsm.clear(message.from_user.id)
    await message.reply(
        messages.channel_saved(fwd.id),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.channel_menu(),
    )


async def _show_settings(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.reply(
        messages.settings_dashboard(),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.settings_menu(),
    )


async def _set_template_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    if not args or args[0] not in ("channel_post", "bot_message"):
        await message.reply(
            messages.error("use /settemplate channel_post or /settemplate bot_message"),
            parse_mode=enums.ParseMode.HTML,
        )
        return

    template_name = args[0]
    fsm.set_state(message.from_user.id, fsm.AWAIT_TEMPLATE, {"template_name": template_name})
    await message.reply(
        messages.template_prompt(template_name),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboards.back_to_main(),
    )


async def _get_template_cmd(client: Client, message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.command[1:]
    name = args[0] if args else "channel_post"
    content = await get_template(name)
    await message.reply(
        messages.template_view(name, content),
        parse_mode=enums.ParseMode.HTML,
    )

