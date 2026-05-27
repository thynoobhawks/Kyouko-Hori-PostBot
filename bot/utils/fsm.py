"""
bot/utils/fsm.py — Lightweight in-memory FSM for multi-step conversations.

States are keyed by user_id. Each entry is a small dict:
    {
        "state": "AWAIT_480P",
        "data":  { ... }          # accumulates session data
    }

Stored in-process only — resets on restart (which is fine; conversations
are short-lived and we persist the final result to MongoDB).
"""

from typing import Any, Optional

_sessions: dict[int, dict] = {}

# ── State names ───────────────────────────────────────────────────────────────
IDLE           = "IDLE"
AWAIT_480P     = "AWAIT_480P"
AWAIT_720P     = "AWAIT_720P"
AWAIT_1080P    = "AWAIT_1080P"
AWAIT_4K       = "AWAIT_4K"
AWAIT_CONFIRM  = "AWAIT_CONFIRM"
AWAIT_CHANNEL  = "AWAIT_CHANNEL"
AWAIT_TEMPLATE = "AWAIT_TEMPLATE"

QUALITY_STATES = [AWAIT_480P, AWAIT_720P, AWAIT_1080P, AWAIT_4K]
QUALITY_LABELS = ["480p", "720p", "1080p", "4K"]

NEXT_QUALITY_STATE = {
    AWAIT_480P:  AWAIT_720P,
    AWAIT_720P:  AWAIT_1080P,
    AWAIT_1080P: AWAIT_4K,
    AWAIT_4K:    AWAIT_CONFIRM,
}


def get_state(user_id: int) -> str:
    return _sessions.get(user_id, {}).get("state", IDLE)


def get_data(user_id: int) -> dict:
    return _sessions.get(user_id, {}).get("data", {})


def set_state(user_id: int, state: str, data: Optional[dict] = None) -> None:
    if user_id not in _sessions:
        _sessions[user_id] = {"state": IDLE, "data": {}}
    _sessions[user_id]["state"] = state
    if data is not None:
        _sessions[user_id]["data"].update(data)


def update_data(user_id: int, **kwargs: Any) -> None:
    if user_id not in _sessions:
        _sessions[user_id] = {"state": IDLE, "data": {}}
    _sessions[user_id]["data"].update(kwargs)


def clear(user_id: int) -> None:
    _sessions.pop(user_id, None)


def quality_label_for_state(state: str) -> str:
    idx = QUALITY_STATES.index(state)
    return QUALITY_LABELS[idx]
