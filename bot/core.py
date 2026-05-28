"""
bot/core.py — Creates and configures the Pyrogram bot client.
All handlers are registered here in one place.
"""

import logging
from pyrogram import Client
from config import config

log = logging.getLogger(__name__)


def _build_client() -> Client:
    """Instantiate a Pyrogram Client in webhook (no-updates) mode."""
    return Client(
        name="anime_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
        # Webhook mode — Pyrogram won't poll; updates come via FastAPI
        no_updates=True,
        in_memory=True,           # avoid session file on Render ephemeral disk
    )


bot: Client = _build_client()


def create_app(client: Client) -> None:
    """Register every handler module onto the client."""
    # Import here to avoid circular imports at module-load time
    from bot.handlers import start, post, settings, callbacks

    start.register(client)
    post.register(client)
    settings.register(client)
    callbacks.register(client)

    log.info("✅ All handlers registered.")
