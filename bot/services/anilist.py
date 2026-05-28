"""
bot/services/anilist.py — AniList GraphQL API integration.
Searches by clean anime title only (episode number stripped before querying).
"""

import logging
import re
import aiohttp
from config import config

log = logging.getLogger(__name__)

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
  }
}
"""


def clean_search_query(raw: str) -> tuple[str, str]:
    """
    Split user input into (anime_title, episode_hint).

    Examples:
      "Naruto 01"               → ("Naruto", "01")
      "Dandadan Episode 08"     → ("Dandadan", "Episode 08")
      "Witch Hat Atelier 01"    → ("Witch Hat Atelier", "01")
      "Attack on Titan S4E12"   → ("Attack on Titan", "S4E12")
    """
    # Match episode patterns at the END of the string
    ep_patterns = [
        r'\s+[Ee]pisode\s+(\d+)$',       # "Episode 08"
        r'\s+[Ee]p\.?\s*(\d+)$',          # "Ep 08" or "Ep. 08"
        r'\s+S\d+[Ee]\d+$',               # "S4E12"
        r'\s+(\d{1,4})$',                  # trailing number "01"
    ]

    episode_hint = ""
    title = raw.strip()

    for pattern in ep_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            episode_hint = title[match.start():].strip()
            title = title[:match.start()].strip()
            break

    return title, episode_hint or raw.split()[-1]


async def fetch_anime(raw_query: str) -> dict | None:
    """
    Search AniList for an anime. Strips episode info before querying.
    Returns a normalised dict or None on failure.
    """
    search_title, episode_hint = clean_search_query(raw_query)
    log.info(f"AniList search: '{search_title}' (episode hint: '{episode_hint}')")

    payload = {"query": QUERY, "variables": {"search": search_title}}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config.ANILIST_API,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15),
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
        log.warning(f"No AniList result for: {search_title!r}")
        return None

    result = _normalise(media)
    # Attach the episode hint so handlers can use it
    result["_episode_hint"] = episode_hint
    return result


def _normalise(media: dict) -> dict:
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
    clean = re.sub(r"<[^>]+>", "", text or "")
    return clean[:350].rstrip() + ("…" if len(clean) > 350 else "")

