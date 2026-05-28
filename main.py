"""
main.py — Entry point for the Anime Auto Post Bot.
Uses Pyrogram in polling mode started as a background task,
with FastAPI only for the health endpoint and keeping Render alive.

NOTE: Pyrogram does not support true webhook update injection.
We run Pyrogram's built-in polling (idle) alongside FastAPI using asyncio.
This is the correct lightweight pattern for Render free tier.
"""

import asyncio
import logging

import uvicorn
from fastapi import FastAPI, Response
from contextlib import asynccontextmanager

from config import config
from bot.core import create_app, bot
from bot.database.mongo import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


async def delete_webhook():
    """Remove any existing webhook so polling works cleanly."""
    import aiohttp
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/deleteWebhook"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"drop_pending_updates": True}) as resp:
            data = await resp.json()
            if data.get("ok"):
                log.info("✅ Webhook deleted — polling mode active.")
            else:
                log.warning(f"deleteWebhook response: {data}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 Starting bot…")
    await db.connect()
    create_app(bot)
    await delete_webhook()
    await bot.start()
    # Run Pyrogram polling in background
    asyncio.create_task(_run_polling())
    yield
    log.info("🛑 Shutting down…")
    await bot.stop()
    await db.close()


async def _run_polling():
    """Keep Pyrogram running — it handles incoming updates via long polling."""
    from pyrogram import idle
    log.info("🔄 Pyrogram polling started.")
    await idle()


app = FastAPI(lifespan=lifespan, title="Anime Bot", docs_url=None, redoc_url=None)


@app.get("/health")
async def health():
    """Keep-alive endpoint for UptimeRobot pings."""
    return {"status": "ok", "bot": config.BOT_USERNAME}


@app.get("/")
async def root():
    return {"status": "running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, log_level="info")
