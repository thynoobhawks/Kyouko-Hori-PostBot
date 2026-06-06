"""
bot/ui/theme.py — Centralized theme system.

All text rendering, small caps conversion, formatting,
and visual constants live here.
"""

# ── Small Caps Unicode Map ────────────────────────────────────────────────────
_SMALL_CAPS = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ',
    'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ',
    'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
    's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
    'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ',
    'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ',
    'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ',
    'S': 'ꜱ', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x',
    'Y': 'ʏ', 'Z': 'ᴢ',
}


def sc(text: str) -> str:
    """Convert text to small caps. Preserves non-alpha characters."""
    return "".join(_SMALL_CAPS.get(c, c) for c in text)


def bold(text: str) -> str:
    return f"<b>{text}</b>"


def italic(text: str) -> str:
    return f"<i>{text}</i>"


def code(text: str) -> str:
    return f"<code>{text}</code>"


def link(label: str, url: str) -> str:
    return f'<a href="{url}">{label}</a>'


def bq(text: str, expandable: bool = False) -> str:
    tag = "blockquote expandable" if expandable else "blockquote"
    return f"<{tag}>{text}</{tag.split()[0]}>"


# ── Divider ───────────────────────────────────────────────────────────────────
DIV = "────────────────────"
DIV_SHORT = "──────────"

# ── Bullet ────────────────────────────────────────────────────────────────────
BULLET = "·"


def bullet(text: str) -> str:
    return f"{BULLET} {text}"


def bullets(items: list[str]) -> str:
    return "\n".join(bullet(i) for i in items)


# ── Header builder ────────────────────────────────────────────────────────────
def header(title: str, subtitle: str = "") -> str:
    out = bold(sc(title))
    if subtitle:
        out += f"\n{italic(sc(subtitle))}"
    return out


# ── Section ───────────────────────────────────────────────────────────────────
def section(title: str, items: list[str]) -> str:
    lines = [bold(sc(title))]
    for item in items:
        lines.append(bullet(sc(item)))
    return "\n".join(lines)


# ── Full message builder ──────────────────────────────────────────────────────
def message(
    title: str,
    subtitle: str = "",
    body_items: list[str] = None,
    note: str = "",
    expandable_body: bool = False,
) -> str:
    parts = [header(title, subtitle)]

    if body_items:
        body_text = bullets([sc(i) for i in body_items])
        if expandable_body:
            parts.append(bq(f"\n{body_text}\n", expandable=True))
        else:
            parts.append(body_text)

    if note:
        parts.append(italic(sc(note)))

    return "\n\n".join(parts)


# ── Welcome image URL ─────────────────────────────────────────────────────────
# Kyouko Hori welcome banner
WELCOME_IMAGE = "https://i.imgur.com/your-hori-image.jpg"  # replace with actual URL
