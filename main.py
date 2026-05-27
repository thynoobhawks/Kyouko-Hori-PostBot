"""
main.py — Entry point for the Anime Auto Post Bot.
Starts FastAPI webhook server + Pyrogram client.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from pyrogram import idle

from config import config
from bot.core import create_app, bot
from bot.database.mongo import db

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and graceful shutdown."""
    log.info("🚀 Starting bot…")
    await db.connect()
    await bot.start()

    # Set webhook
    webhook_url = f"{config.WEBHOOK_URL}/webhook/{config.BOT_TOKEN}"
    await bot.set_webhook(webhook_url)
    log.info(f"✅ Webhook set → {webhook_url}")

    yield  # ── server is running ──

    log.info("🛑 Shutting down…")
    await bot.stop()
    await db.close()


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(lifespan=lifespan, title="Anime Bot Webhook", docs_url=None, redoc_url=None)

# Register all Pyrogram handlers
create_app(bot)


@app.post(f"/webhook/{config.BOT_TOKEN}")
async def webhook(request: Request):
    """Receive Telegram updates via webhook."""
    try:
        data = await request.json()
        await bot.handle_update(data)
    except Exception as e:
        log.error(f"Webhook error: {e}")
    return Response(status_code=200)


@app.get("/health")
async def health():
    """Render keep-alive health check endpoint."""
    return {"status": "ok", "bot": config.BOT_USERNAME}


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        log_level="info",
    )
