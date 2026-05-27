"""
bot/utils/html.py — Safe HTML helpers for Telegram messages.
"""

import html


def escape_html(text: str) -> str:
    """Escape characters that break Telegram HTML mode."""
    return html.escape(str(text))


def bold(text: str) -> str:
    return f"<b>{escape_html(text)}</b>"


def italic(text: str) -> str:
    return f"<i>{escape_html(text)}</i>"


def code(text: str) -> str:
    return f"<code>{escape_html(text)}</code>"


def link(label: str, url: str) -> str:
    return f'<a href="{url}">{escape_html(label)}</a>'


SEPARATOR = "─────────────────────"
