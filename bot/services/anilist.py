"""
bot/services/anilist.py — AniList GraphQL API integration.
Fetches anime metadata: title, cover, synopsis, genres, rating, etc.
"""

import logging
import aiohttp
from config import config

log = logging.getLogger(__name__)

# ── GraphQL Query ─────────────────────────────────────────────────────────────
QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME, sort: SEARCH_MATCH) {
    id
    title {
      romaji
      english
      native
    }
    description(asHtml: false)
    coverImage {
      large
      extraLarge
    }
    bannerImage
    genres
    status
    season
    seasonYear
    episodes
    averageScore
    popularity
    studios(isMain: true) {
      nodes { name }
    }
    nextAiringEpisode {
      episode
      airingAt
    }
  }
}
"""


async def fetch_anime(search_query: str) -> dict | None:
    """
    Search AniList for an anime by name.
    Returns a normalised dict or None on failure.
    """
    payload = {"query": QUERY, "variables": {"search": search_query}}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config.ANILIST_API,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    log.error(f"AniList returned HTTP {resp.status}")
                    return None

                data = await resp.json()

    except Exception as e:
        log.error(f"AniList request failed: {e}")
        return None

    try:
        media = data["data"]["Media"]
    except (KeyError, TypeError):
        log.warning(f"No AniList result for: {search_query!r}")
        return None

    return _normalise(media)


def _normalise(media: dict) -> dict:
    """Flatten the AniList response into a clean, flat dict."""
    title = media.get("title", {})
    cover = media.get("coverImage", {})
    studios = media.get("studios", {}).get("nodes", [])

    return {
        "anilist_id": media.get("id"),
        "title_romaji": title.get("romaji", "Unknown"),
        "title_english": title.get("english") or title.get("romaji", "Unknown"),
        "title_native": title.get("native", ""),
        "synopsis": _clean_synopsis(media.get("description", "")),
        "cover_image": cover.get("extraLarge") or cover.get("large", ""),
        "banner_image": media.get("bannerImage", ""),
        "genres": media.get("genres", []),
        "status": media.get("status", "UNKNOWN"),
        "season": media.get("season") or "?",
        "season_year": media.get("seasonYear") or "",
        "total_episodes": media.get("episodes") or "?",
        "rating": media.get("averageScore") or "N/A",
        "popularity": media.get("popularity") or 0,
        "studio": studios[0]["name"] if studios else "Unknown",
    }


def _clean_synopsis(text: str) -> str:
    """Strip HTML tags from AniList synopsis."""
    import re
    clean = re.sub(r"<[^>]+>", "", text or "")
    # Truncate to keep messages short
    return clean[:350].rstrip() + ("…" if len(clean) > 350 else "")
