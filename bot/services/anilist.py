"""
bot/services/anilist.py — AniList GraphQL API integration.
Returns both raw bot data and card-ready formatted data.
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
    title { romaji english native }
    description(asHtml: false)
    coverImage { large extraLarge medium }
    bannerImage
    genres
    status
    season
    seasonYear
    episodes
    averageScore
    popularity
    format
    studios {
      nodes { name isAnimationStudio }
    }
  }
}
"""

# ── Genre side labels ─────────────────────────────────────────────────────────
GENRE_LABELS = {
    "Action": "ACTION BEGINS", "Adventure": "ADVENTURE AWAITS",
    "Fantasy": "FANTASY CALLS", "Romance": "ROMANCE BLOOMS",
    "Comedy": "COMEDY STRIKES", "Thriller": "THRILLER AWAITS",
    "Horror": "HORROR LURKS", "Sci-Fi": "SCI-FI AWAITS",
    "Mystery": "MYSTERY UNFOLDS", "Drama": "DRAMA UNFOLDS",
    "Sports": "SPORTS RISE", "Music": "MUSIC RESONATES",
    "Slice of Life": "LIFE UNFOLDS", "Psychological": "MIND BENDS",
    "Supernatural": "BEYOND REALITY", "Mecha": "MECHS RISE",
    "Magic": "MAGIC AWAITS", "Military": "WAR CALLS",
    "School": "SCHOOL DAYS", "Isekai": "ISEKAI BEGINS",
    "Historical": "HISTORY CALLS",
}

# ── Long title replacements ───────────────────────────────────────────────────
TITLE_REPLACEMENTS = {
    "I WAS REINCARNATED AS THE 7TH PRINCE SO I CAN TAKE MY TIME PERFECTING MY MAGICAL ABILITY": "I WAS REINCARNATED AS THE 7TH PRINCE",
    "HELL MODE: THE HARDCORE GAMER DOMINATES IN ANOTHER WORLD WITH GARBAGE BALANCING": "HELL MODE",
    "THE WORLD'S FINEST ASSASSIN GETS REINCARNATED IN ANOTHER WORLD AS AN ARISTOCRAT": "THE WORLD'S FINEST ASSASSIN",
    "BANISHED FROM THE HERO'S PARTY, I DECIDED TO LIVE A QUIET LIFE IN THE COUNTRYSIDE": "BANISHED FROM THE HERO'S PARTY",
    "MY INSTANT DEATH ABILITY IS SO OVERPOWERED, NO ONE IN THIS OTHER WORLD STANDS A CHANCE AGAINST ME!": "MY INSTANT DEATH ABILITY",
    "RE:ZERO -STARTING LIFE IN ANOTHER WORLD- SEASON 3": "RE:ZERO SEASON 3",
    "RE:ZERO -STARTING LIFE IN ANOTHER WORLD- SEASON 4": "RE:ZERO SEASON 4",
}


def get_side_label(genres: list) -> str:
    for genre in genres:
        if genre in GENRE_LABELS:
            return GENRE_LABELS[genre]
    return "ANIME AWAITS"


def clean_search_query(raw: str) -> tuple[str, str]:
    """Split user input into (anime_title, episode_hint)."""
    ep_patterns = [
        r'\s+[Ee]pisode\s+(\d+)$',
        r'\s+[Ee]p\.?\s*(\d+)$',
        r'\s+S\d+[Ee]\d+$',
        r'\s+(\d{1,4})$',
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
    Fetch anime from AniList. Returns merged dict with both
    bot fields and card-ready fields.
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

    result = _build_full_data(media)
    result["_episode_hint"] = episode_hint
    return result


def _build_full_data(media: dict) -> dict:
    """Build complete data dict for both bot messages and card generation."""
    title = media.get("title", {})
    cover = media.get("coverImage", {})
    studio_nodes = media.get("studios", {}).get("nodes", [])
    genres = (media.get("genres") or [])[:5] or ["Anime"]

    # ── Raw titles ────────────────────────────────────────────────────────────
    title_romaji = title.get("romaji") or "Unknown"
    title_english = title.get("english") or title_romaji

    # ── Card-formatted titles ─────────────────────────────────────────────────
    title_up = (
        title_english
        .replace("Season ", "S")
        .replace("Part ", "P")
        .replace("Cour ", "C")
        .upper()
    )
    title_up = TITLE_REPLACEMENTS.get(title_up, title_up)
    romaji_up = title_romaji.upper()

    title_class = (
        "title-xl" if len(title_up) <= 9 else
        "title-lg" if len(title_up) <= 18 else
        "title-md" if len(title_up) <= 34 else
        "title-sm"
    )

    # ── Studio ────────────────────────────────────────────────────────────────
    animation_studios = [s["name"] for s in studio_nodes if s.get("isAnimationStudio")]
    studio = (
        animation_studios[0] if animation_studios
        else (studio_nodes[0]["name"] if studio_nodes else "Unknown Studio")
    )

    # ── Season ────────────────────────────────────────────────────────────────
    season_name = media.get("season") or ""
    season_year = media.get("seasonYear") or ""
    season_label = f"{season_name.capitalize()} {season_year}".strip() or "N/A"

    # ── Metadata ──────────────────────────────────────────────────────────────
    score = media.get("averageScore")
    rating_str = f"{score}%" if score else "N/A"
    episodes = str(media.get("episodes") or "N/A")
    anime_format = (media.get("format") or "TV").replace("_", " ").replace("TV SHORT", "TV")

    # ── Cover image ───────────────────────────────────────────────────────────
    cover_image = cover.get("extraLarge") or cover.get("large") or cover.get("medium") or ""

    # ── Synopsis ──────────────────────────────────────────────────────────────
    raw_desc = _clean_html(media.get("description") or "")
    description = raw_desc[:320].rsplit(" ", 1)[0] + "…" if len(raw_desc) > 320 else raw_desc

    return {
        # ── Bot message fields ────────────────────────────────────────────────
        "anilist_id": media.get("id"),
        "title_romaji": title_romaji,
        "title_english": title_english,
        "title_native": title.get("native", ""),
        "synopsis": description,
        "cover_image": cover_image,
        "genres": genres,
        "status": media.get("status", "UNKNOWN"),
        "season": season_name or "?",
        "season_year": season_year,
        "total_episodes": media.get("episodes") or "?",
        "rating": score or "N/A",
        "studio": studio,

        # ── Card generation fields ────────────────────────────────────────────
        "title_english_card": title_up,
        "title_romaji_card": romaji_up,
        "title_class": title_class,
        "season_display": season_label,
        "season_header": season_label.upper(),
        "format": anime_format,
        "episodes_card": episodes,
        "rating_card": rating_str,
        "description": description,
        "poster": cover_image,
        "side_label": get_side_label(genres),
        "show_romaji": romaji_up != title_up,
    }


def _clean_html(text: str) -> str:
    clean = re.sub(r"<br\s*/?>", " ", text)
    clean = re.sub(r"<[^>]+>", "", clean)
    for old, new in {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&#039;": "'", "&quot;": '"', "&nbsp;": " "}.items():
        clean = clean.replace(old, new)
    return re.sub(r"\s+", " ", clean).strip()
