"""
bot/ui/keyboards.py — Centralized inline keyboard builder.

All button layouts defined here. Handlers reference these
instead of building keyboards inline.
"""

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.ui.theme import sc


def btn(label: str, data: str = None, url: str = None) -> InlineKeyboardButton:
    """Single button. Either callback_data or url."""
    if url:
        return InlineKeyboardButton(sc(label), url=url)
    return InlineKeyboardButton(sc(label), callback_data=data)


def row(*buttons: InlineKeyboardButton) -> list:
    return list(buttons)


def kb(*rows) -> InlineKeyboardMarkup:
    """Build keyboard from rows of buttons."""
    return InlineKeyboardMarkup(list(rows))


# ── Main Menu ─────────────────────────────────────────────────────────────────
def main_menu() -> InlineKeyboardMarkup:
    return kb(
        row(btn("create post", "menu:post")),
        row(btn("upload content", "menu:upload")),
        row(btn("channels", "menu:channels"), btn("analytics", "menu:analytics")),
        row(btn("templates", "menu:templates"), btn("links", "menu:links")),
        row(btn("settings", "menu:settings")),
    )


# ── Post Creator ──────────────────────────────────────────────────────────────
def post_creator_menu() -> InlineKeyboardMarkup:
    return kb(
        row(btn("continue", "post:start")),
        row(btn("back", "menu:main")),
    )


def quality_selector(selected: list[str] = None) -> InlineKeyboardMarkup:
    selected = selected or []
    qualities = ["480p", "720p", "1080p", "2160p"]
    rows = []
    for q in qualities:
        tick = "· " if q in selected else "  "
        rows.append(row(btn(f"{tick}{q}", f"quality:toggle:{q}")))
    rows.append(row(btn("confirm", "quality:confirm"), btn("back", "post:start")))
    return kb(*rows)


def post_confirm_menu(uid: int) -> InlineKeyboardMarkup:
    return kb(
        row(btn("publish", f"confirm_post:{uid}"), btn("cancel", f"cancel_post:{uid}")),
        row(btn("back", "post:start")),
    )


def skip_cancel_row() -> InlineKeyboardMarkup:
    return kb(row(btn("skip", "step:skip"), btn("cancel", "step:cancel")))


# ── Upload ────────────────────────────────────────────────────────────────────
def upload_menu() -> InlineKeyboardMarkup:
    return kb(
        row(btn("select anime", "upload:anime")),
        row(btn("upload files", "upload:files")),
        row(btn("set qualities", "upload:quality")),
        row(btn("attach links", "upload:links")),
        row(btn("preview", "upload:preview")),
        row(btn("publish", "upload:publish")),
        row(btn("back", "menu:main")),
    )


# ── Channels ──────────────────────────────────────────────────────────────────
def channel_menu() -> InlineKeyboardMarkup:
    return kb(
        row(btn("add channel", "ch:add")),
        row(btn("remove channel", "ch:remove")),
        row(btn("set default template", "ch:template")),
        row(btn("set default links", "ch:links")),
        row(btn("broadcast status", "ch:broadcast")),
        row(btn("back", "menu:main")),
    )


# ── Templates ─────────────────────────────────────────────────────────────────
def template_menu() -> InlineKeyboardMarkup:
    return kb(
        row(btn("channel post", "tpl:channel_post")),
        row(btn("bot message", "tpl:bot_message")),
        row(btn("view current", "tpl:view")),
        row(btn("reset to default", "tpl:reset")),
        row(btn("back", "menu:main")),
    )


# ── Links ─────────────────────────────────────────────────────────────────────
def links_menu() -> InlineKeyboardMarkup:
    return kb(
        row(btn("add custom link", "link:add")),
        row(btn("view links", "link:view")),
        row(btn("remove link", "link:remove")),
        row(btn("back", "menu:main")),
    )


# ── Settings ──────────────────────────────────────────────────────────────────
def settings_menu() -> InlineKeyboardMarkup:
    return kb(
        row(btn("appearance", "set:appearance")),
        row(btn("auto posting", "set:auto")),
        row(btn("channel preferences", "set:channels")),
        row(btn("broadcast settings", "set:broadcast")),
        row(btn("admin tools", "set:admin")),
        row(btn("back", "menu:main")),
    )


# ── Analytics ─────────────────────────────────────────────────────────────────
def analytics_menu() -> InlineKeyboardMarkup:
    return kb(
        row(btn("total posts", "ana:posts")),
        row(btn("total users", "ana:users")),
        row(btn("back", "menu:main")),
    )


# ── Quality buttons for channel post ─────────────────────────────────────────
def quality_buttons(qualities: dict[str, str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(q.upper(), url=url)]
        for q, url in qualities.items()
    ]
    return InlineKeyboardMarkup(rows)


# ── Download button for channel post ─────────────────────────────────────────
def download_button(url: str) -> InlineKeyboardMarkup:
    return kb(row(btn("download", url=url)))


# ── Back only ─────────────────────────────────────────────────────────────────
def back_to_main() -> InlineKeyboardMarkup:
    return kb(row(btn("back", "menu:main")))
