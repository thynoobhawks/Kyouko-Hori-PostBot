"""
bot/core.py — Bot client and handler registration.
"""

import logging
from pyrogram import Client
from config import config

log = logging.getLogger(__name__)


def _build_client() -> Client:
    return Client(
        name="anime_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        in_memory=True,
    )


bot: Client = _build_client()


def create_app(client: Client) -> None:
    from bot.handlers import start, post, settings, callbacks, broadcast, text_router, menu

    start.register(client)
    post.register(client)
    settings.register(client)
    menu.register(client)        # dashboard navigation
    callbacks.register(client)
    broadcast.register(client)
    text_router.register(client) # always last

    log.info("✅ All handlers registered.")
