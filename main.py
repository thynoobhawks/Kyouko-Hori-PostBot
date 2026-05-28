"""
main.py — Entry point for the Anime Auto Post Bot.
Starts FastAPI webhook server + Pyrogram client.
"""

import asyncio
import logging
import aiohttp

import uvicorn
from fastapi import FastAPI, Request, Response

from config import config
from bot.core import create_app, bot
from bot.database.mongo import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


async def set_webhook():
    """Register webhook with Telegram directly via Bot API."""
    webhook_url = f"{config.WEBHOOK_URL}/webhook/{config.BOT_TOKEN}"
    api_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/setWebhook"

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json={"url": webhook_url}) as resp:
            data = await resp.json()
            if data.get("ok"):
                log.info(f"✅ Webhook set → {webhook_url}")
            else:
                log.error(f"❌ Webhook failed: {data}")


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 Starting bot…")
    await db.connect()
    await bot.start()
    await set_webhook()
    create_app(bot)
    yield
    log.info("🛑 Shutting down…")
    await bot.stop()
    await db.close()


app = FastAPI(lifespan=lifespan, title="Anime Bot Webhook", docs_url=None, redoc_url=None)


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
    return {"status": "ok", "bot": config.BOT_USERNAME}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, log_level="info")
