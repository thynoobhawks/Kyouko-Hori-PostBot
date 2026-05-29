"""
bot/database/mongo.py — Async MongoDB client using Motor.
All data persists on MongoDB Atlas across Render redeployments.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import config

log = logging.getLogger(__name__)


class MongoDB:
    def __init__(self):
        self._client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None

    async def connect(self):
        log.info("Connecting to MongoDB Atlas…")
        self._client = AsyncIOMotorClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        self.db = self._client[config.DB_NAME]
        await self._client.admin.command("ping")
        log.info("✅ MongoDB connected.")
        await self._ensure_indexes()

    async def _ensure_indexes(self):
        await self.db.anime_posts.create_index("deep_link_id", unique=True)
        await self.db.anime_posts.create_index("created_at")
        await self.db.settings.create_index("key", unique=True)
        await self.db.templates.create_index("name", unique=True)
        # Users — permanent storage for broadcast
        await self.db.users.create_index("user_id", unique=True)
        log.info("✅ MongoDB indexes ensured.")

    async def close(self):
        if self._client:
            self._client.close()

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

    @property
    def users(self):
        return self.db["users"]


db = MongoDB()
