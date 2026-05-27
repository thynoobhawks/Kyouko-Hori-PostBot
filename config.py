"""
config.py — All environment-based configuration.
Load with python-dotenv locally; Render injects vars in production.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # ── Telegram ──────────────────────────────────────────────────────────────
    BOT_TOKEN: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])
    BOT_USERNAME: str = field(default_factory=lambda: os.environ["BOT_USERNAME"])
    API_ID: int = field(default_factory=lambda: int(os.environ["API_ID"]))
    API_HASH: str = field(default_factory=lambda: os.environ["API_HASH"])

    # ── Admin IDs (comma-separated) ───────────────────────────────────────────
    ADMIN_IDS: list[int] = field(
        default_factory=lambda: [
            int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
        ]
    )

    # ── MongoDB ───────────────────────────────────────────────────────────────
    MONGO_URI: str = field(default_factory=lambda: os.environ["MONGO_URI"])
    DB_NAME: str = field(default_factory=lambda: os.getenv("DB_NAME", "animebot"))

    # ── Webhook / Server ──────────────────────────────────────────────────────
    WEBHOOK_URL: str = field(
        default_factory=lambda: os.environ["WEBHOOK_URL"].rstrip("/")
    )
    PORT: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # ── AniList ───────────────────────────────────────────────────────────────
    ANILIST_API: str = "https://graphql.anilist.co"


config = Config()
