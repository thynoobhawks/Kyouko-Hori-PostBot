"""
bot/services/card_generator.py — Generates anime info card as PNG.

Uses Playwright (headless Chromium) to render anime.html + styles.css
into a 1280x720 PNG image, then returns the image bytes.

The card is auto-generated from AniList data and used as the
default post image when no custom poster is provided by admin.
"""

import asyncio
import base64
import logging
import os
from pathlib import Path

import aiohttp

log = logging.getLogger(__name__)

# Template paths
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
HTML_TEMPLATE = TEMPLATES_DIR / "anime.html"
CSS_FILE = TEMPLATES_DIR / "styles.css"


async def generate_card(anime_data: dict) -> bytes | None:
    """
    Render the anime card HTML to a PNG image.
    Returns PNG bytes or None on failure.
    
    anime_data keys expected (from anilist.py fetch_anime_data):
        title_english, title_romaji, title_class, season_display,
        season_header, format, episodes, rating, genres, studio,
        description, poster, side_label, show_romaji
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None

    # Download poster image and convert to base64
    poster_b64 = await _get_poster_b64(anime_data.get("poster", ""))

    # Load CSS
    css_content = CSS_FILE.read_text(encoding="utf-8")

    # Load and render HTML template
    from jinja2 import Template
    html_template = HTML_TEMPLATE.read_text(encoding="utf-8")
    template = Template(html_template)

    html = template.render(
        css=css_content,
        poster_b64=poster_b64,
        **anime_data,
    )

    # Render with Playwright
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            page = await browser.new_page(viewport={"width": 1280, "height": 720})

            await page.set_content(html, wait_until="networkidle")

            # Wait for Google Fonts to load
            await asyncio.sleep(1.5)

            screenshot = await page.screenshot(
                type="png",
                clip={"x": 0, "y": 0, "width": 1280, "height": 720},
            )

            await browser.close()

        log.info(f"✅ Card generated for: {anime_data.get('title_english', '?')}")
        return screenshot

    except Exception as e:
        log.error(f"Playwright render failed: {e}")
        return None


async def _get_poster_b64(url: str) -> str:
    """Download poster image and return as base64 data URI."""
    if not url:
        return ""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    b64 = base64.b64encode(image_bytes).decode("utf-8")
                    content_type = resp.content_type or "image/jpeg"
                    return f"data:{content_type};base64,{b64}"
    except Exception as e:
        log.warning(f"Failed to download poster: {e}")
    return ""
