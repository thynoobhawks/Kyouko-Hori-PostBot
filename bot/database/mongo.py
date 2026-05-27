"""
bot/database/mongo.py — Async MongoDB client using Motor.
Provides a single shared `db` instance used across the app.
Data is stored on MongoDB Atlas so it survives redeployments.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import config

log = logging.getLogger(__name__)


class MongoDB:
    """Thin wrapper around Motor so we can connect/disconnect cleanly."""

    def __init__(self):
        self._client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None

    async def connect(self):
        log.info("Connecting to MongoDB Atlas…")
        self._client = AsyncIOMotorClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        self.db = self._client[config.DB_NAME]
        # Validate connection
        await self._client.admin.command("ping")
        log.info("✅ MongoDB connected.")

        # Ensure indexes
        await self._ensure_indexes()

    async def _ensure_indexes(self):
        await self.db.anime_posts.create_index("deep_link_id", unique=True)
        await self.db.anime_posts.create_index("created_at")
        await self.db.settings.create_index("key", unique=True)

    async def close(self):
        if self._client:
            self._client.close()
            log.info("MongoDB connection closed.")

    # ── Convenience shorthand properties ─────────────────────────────────────

    @property
    def settings(self):
        return self.db["settings"]

    @property
    def anime_posts(self):
        return self.db["anime_posts"]

    @property
    def templates(self):
        return self.db["templates"]

    @property
    def channels(self):
        return self.db["channels"]


db = MongoDB()
