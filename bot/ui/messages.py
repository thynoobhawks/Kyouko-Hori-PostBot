"""
bot/ui/messages.py — All UI message strings.
"""

from bot.ui.theme import (
    sc, bold, italic, bq, bullets, bullet,
    header, DIV, BULLET
)


# ── Welcome ───────────────────────────────────────────────────────────────────

def welcome(first_name: str) -> str:
    items = [
        "create anime posts automatically",
        "upload content manually",
        "generate custom redirect links",
        "manage channels from one dashboard",
        "publish multiple qualities with a single workflow",
    ]
    return (
        f"{bold(sc('welcome'))}, {first_name}\n"
        f"{italic(sc('i am your anime publishing assistant'))}\n\n"
        f"{DIV}\n\n"
        f"{bullets(items)}\n\n"
        f"{bq(italic(sc('select an option below to get started')), expandable=True)}"
    )


# ── Main Menu ─────────────────────────────────────────────────────────────────

def main_menu() -> str:
    return (
        f"{bold(sc('main dashboard'))}\n\n"
        f"{italic(sc('select a module to continue'))}"
    )


# ── Post Creator ──────────────────────────────────────────────────────────────

def post_creator() -> str:
    items = [
        "create a new anime post",
        "select quality options",
        "configure redirect links",
        "publish to your channel instantly",
    ]
    return f"{bold(sc('post creator'))}\n\n{bullets(items)}"


def post_fetching(query: str) -> str:
    return (
        f"{bold(sc('searching'))}\n\n"
        f"{bullet(sc('fetching data from anilist'))}\n"
        f"{bullet(italic(query))}"
    )


def post_found(anime: dict, episode: str) -> str:
    genres = ", ".join(anime.get("genres", [])[:4]) or "n/a"
    synopsis = anime.get("synopsis", "")
    return (
        f"{bold(sc('anime found'))}\n\n"
        f"{bold(anime['title_romaji'])}\n"
        f"{italic(anime['title_english'])}\n\n"
        f"{DIV}\n\n"
        f"{bullet(sc('episode'))} · {episode}\n"
        f"{bullet(sc('season'))} · {anime.get('season', '?')} {anime.get('season_year', '')}\n"
        f"{bullet(sc('episodes'))} · {anime.get('total_episodes', '?')}\n"
        f"{bullet(sc('rating'))} · {anime.get('rating', 'n/a')}/100\n"
        f"{bullet(sc('genres'))} · {genres}\n\n"
        f"{bq(italic(synopsis), expandable=True)}"
    )


def post_custom_media() -> str:
    items = [
        "send a photo or video to use as post media",
        "or skip to use the auto-generated card",
    ]
    return f"{bold(sc('custom poster'))}\n\n{bullets(items)}"


def post_quality_prompt(label: str) -> str:
    return (
        f"{bold(sc('quality link'))}\n\n"
        f"{bullet(sc('send the'))} {bold(label.upper())} {sc('download link')}\n"
        f"{bullet(sc('or skip to continue without it'))}"
    )


def post_quality_saved(label: str, next_label: str) -> str:
    return (
        f"{bold(sc('saved'))}\n\n"
        f"{bullet(label)} {sc('link saved')}\n\n"
        f"{bullet(sc('now send the'))} {bold(next_label.upper())} {sc('link')}\n"
        f"{bullet(sc('or skip to continue'))}"
    )


def post_skipped(label: str, next_label: str) -> str:
    return (
        f"{sc('skipped')} {bold(label)}\n\n"
        f"{bullet(sc('send the'))} {bold(next_label.upper())} {sc('link')}\n"
        f"{bullet(sc('or skip to continue'))}"
    )


def post_preview(anime: dict, episode: str, qualities: dict, media_source: str) -> str:
    quality_list = "\n".join(f"{BULLET} {k}" for k in qualities.keys()) if qualities else f"{BULLET} none"
    return (
        f"{bold(sc('preview'))}\n\n"
        f"{bold(anime['title_romaji'])}\n"
        f"{italic(anime['title_english'])}\n\n"
        f"{DIV}\n\n"
        f"{bullet(sc('episode'))} · {episode}\n"
        f"{bullet(sc('season'))} · {anime.get('season', '?')}\n"
        f"{bullet(sc('media'))} · {sc(media_source)}\n\n"
        f"{bold(sc('qualities'))}\n"
        f"{quality_list}\n\n"
        f"{DIV}\n\n"
        f"{italic(sc('confirm to publish to your channel'))}"
    )


def post_publishing() -> str:
    return f"{bold(sc('publishing'))}\n\n{bullet(sc('sending to channel'))}"


def post_published(bot_link: str) -> str:
    return (
        f"{bold(sc('published'))}\n\n"
        f"{bullet(sc('your post is now live'))}\n\n"
        f"{bullet(sc('deep link'))}\n"
        f"<code>{bot_link}</code>"
    )


def post_failed() -> str:
    return (
        f"{bold(sc('publish failed'))}\n\n"
        f"{bullet(sc('check bot channel permissions'))}\n"
        f"{bullet(sc('verify the channel id is correct'))}"
    )


def post_cancelled() -> str:
    return f"{bold(sc('cancelled'))}\n\n{bullet(sc('post creation has been cancelled'))}"


def post_not_found(query: str) -> str:
    return (
        f"{bold(sc('not found'))}\n\n"
        f"{bullet(sc('no results for'))} {italic(query)}\n\n"
        f"{bold(sc('tips'))}\n"
        f"{bullet(sc('use the exact anime title'))}\n"
        f"{bullet(sc('try english or romaji'))}\n"
        f"{bullet(sc('remove the episode number'))}"
    )


# ── Channel ───────────────────────────────────────────────────────────────────

def channel_dashboard(channel_id=None) -> str:
    status = sc(str(channel_id)) if channel_id else italic(sc("not configured"))
    items = [
        "add or remove channels",
        "edit channel settings",
        "set default templates",
        "configure broadcast options",
    ]
    return (
        f"{bold(sc('channel dashboard'))}\n\n"
        f"{bullet(sc('active channel'))} · {status}\n\n"
        f"{bullets(items)}"
    )


def channel_set_prompt() -> str:
    return (
        f"{bold(sc('add channel'))}\n\n"
        f"{bullet(sc('forward a message from the target channel'))}\n"
        f"{bullet(sc('or send the channel id directly'))}\n\n"
        f"{italic(sc('example'))} · <code>-1001234567890</code>"
    )


def channel_saved(channel_id: int) -> str:
    return (
        f"{bold(sc('channel saved'))}\n\n"
        f"{bullet(sc('active channel'))} · <code>{channel_id}</code>"
    )


# ── Templates ─────────────────────────────────────────────────────────────────

def template_dashboard() -> str:
    items = [
        "edit channel post template",
        "edit bot message template",
        "view current templates",
        "reset to defaults",
    ]
    return f"{bold(sc('templates'))}\n\n{bullets(items)}"


def template_prompt(name: str) -> str:
    vars_line = (
        "<code>{title}</code>  <code>{english_title}</code>  <code>{episode}</code>\n"
        "<code>{season}</code>  <code>{year}</code>  <code>{genres}</code>\n"
        "<code>{rating}</code>  <code>{total_episodes}</code>  <code>{studio}</code>\n"
        "<code>{qualities}</code>  <code>{download_link}</code>"
    )
    return (
        f"{bold(sc('edit template'))} · {bold(name)}\n\n"
        f"{bold(sc('available variables'))}\n"
        f"{vars_line}\n\n"
        f"{italic(sc('send your new template text below'))}\n"
        f"{italic(sc('do not include {cover_image}'))}"
    )


def template_saved(name: str) -> str:
    return f"{bold(sc('template saved'))}\n\n{bullet(name)} {sc('has been updated')}"


def template_view(name: str, content: str) -> str:
    from bot.utils.html import escape_html
    return (
        f"{bold(sc('current template'))} · {bold(name)}\n\n"
        f"<code>{escape_html(content)}</code>"
    )


# ── Settings ──────────────────────────────────────────────────────────────────

def settings_dashboard() -> str:
    items = [
        "appearance options",
        "auto posting configuration",
        "channel preferences",
        "broadcast settings",
        "admin tools",
    ]
    return f"{bold(sc('settings'))}\n\n{bullets(items)}"


# ── Analytics ─────────────────────────────────────────────────────────────────

def analytics_dashboard(post_count: int, user_count: int) -> str:
    return (
        f"{bold(sc('analytics'))}\n\n"
        f"{bullet(sc('total posts'))} · {bold(str(post_count))}\n"
        f"{bullet(sc('total users'))} · {bold(str(user_count))}"
    )


# ── Broadcast ─────────────────────────────────────────────────────────────────

def broadcast_prompt() -> str:
    items = [
        "send your message below",
        "supports text, photo, and video",
    ]
    return (
        f"{bold(sc('broadcast'))}\n\n"
        f"{bullets(items)}\n\n"
        f"{italic(sc('html formatting is supported'))}"
    )


def broadcast_sending(total: int) -> str:
    return (
        f"{bold(sc('broadcasting'))}\n\n"
        f"{bullet(sc('sending to'))} {bold(str(total))} {sc('users')}"
    )


def broadcast_done(success: int, failed: int) -> str:
    return (
        f"{bold(sc('broadcast complete'))}\n\n"
        f"{bullet(sc('delivered'))} · {bold(str(success))}\n"
        f"{bullet(sc('failed'))} · {bold(str(failed))}"
    )


# ── Generic ───────────────────────────────────────────────────────────────────

def error(text: str) -> str:
    return f"{bold(sc('error'))}\n\n{bullet(sc(text))}"


def loading(action: str = "loading") -> str:
    return italic(sc(action))


def nothing_to_skip() -> str:
    return f"{bold(sc('nothing to skip'))}\n\n{bullet(sc('no active step found'))}"


def no_channel() -> str:
    return (
        f"{bold(sc('no channel configured'))}\n\n"
        f"{bullet(sc('use the channels menu to add a channel first'))}"
    )
