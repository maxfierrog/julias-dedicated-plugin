"""User settings, stored in the collection config so they sync via AnkiWeb
and follow her between computers.

- Missing keys fall back to DEFAULTS, so new settings added in updates
  appear automatically; only values that differ from defaults are stored.
- Every value is validated on read (known choices, clamped numbers, checked
  lists), so a bad value from sync, an older version or a malicious page
  can never break the UI or inject markup.
- Settings are stored per section (one config key each, plus one for
  timeline events). Anki syncs config key by key, newest wins, so edits on
  two computers only collide when they touch the same section.
- Keys this version doesn't know are kept, so an older add-on version on
  another computer never deletes settings a newer version added.
"""

import copy
import datetime as dt
import math
import re
from typing import Any

LEGACY_KEY = "jdp_settings"  # single-key format used before per-section keys
PREFIX = "jdp."

DEFAULTS: dict[str, Any] = {
    "name": "Julia",
    "modules": {
        "theme": True,
        "cards": True,
        "session": True,
        "briefing": True,
        "fatigue": False,
    },
    "theme": {
        "preset": "periwinkle",
        "accent": "",  # "" = the preset's own accent
        "ui_font": "rounded",
        "radius": 16,
        "density": "comfortable",
    },
    "cards": {
        "font": "atkinson",
        "size": 22,
        "width": "medium",
        "align": "auto",
        "surface": "sheet",
        "override_colors": True,
        "dark_images": "dim",
    },
    "session": {
        "show_progress": True,
        "show_eta": True,
        "focus_mode": True,  # hide the top toolbar while reviewing
    },
    "briefing": {
        "greeting": True,
    },
    "home": {
        # Widgets on the home grid, in order (see briefing.WIDGETS). An entry
        # is "id" (default size) or "id:COLSxROWS" for another allowed size.
        "widgets": [
            "timeline",
            "forecast",
            "streak",
            "goal",
            "retention",
            "backlog",
            "heatmap",
        ],
        "goal_minutes": 30,
        # Timeline events: [{"title": str, "date": "YYYY-MM-DD", "deck": int?}]
        "events": [],
    },
}

# Storage units, most specific first: each is saved under its own config key.
UNITS = (
    "home.events",
    "name",
    "modules",
    "theme",
    "cards",
    "session",
    "briefing",
    "home",
)

CHOICES = {
    "theme.preset": {"periwinkle", "peach", "matcha", "berry", "sky", "paper"},
    "theme.ui_font": {"rounded", "playful", "inter", "system"},
    "theme.density": {"compact", "comfortable"},
    "cards.font": {"nunito", "atkinson", "literata", "inter", "system"},
    "cards.width": {"narrow", "medium", "wide"},
    "cards.align": {"auto", "center", "left"},
    "cards.surface": {"sheet", "plain"},
    "cards.dark_images": {"none", "dim", "invert"},
}
RANGES = {
    "theme.radius": (0, 28),
    "cards.size": (14, 36),
    "home.goal_minutes": (5, 600),
}
MAX_NAME = 40
MAX_WIDGETS = 24
MAX_EVENTS = 100
MAX_EVENT_TITLE = 60
MAX_EVENT_YEARS = 10
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_WIDGET = re.compile(r"^[a-z_]{1,32}(:[1-3]x[1-2])?$")


def _valid_events(value) -> list | None:
    if not isinstance(value, list):
        return None
    out = []
    for e in value[:MAX_EVENTS]:
        if not isinstance(e, dict):
            continue
        title, date = e.get("title"), e.get("date")
        if not isinstance(title, str) or not title.strip():
            continue
        try:
            dt.date.fromisoformat(str(date))
        except ValueError:
            continue
        event = {"title": title.strip()[:MAX_EVENT_TITLE], "date": str(date)}
        deck = e.get("deck")
        if isinstance(deck, int) and not isinstance(deck, bool):
            event["deck"] = deck
        out.append(event)
    return out


def _validate(path: str, value: Any, default: Any) -> Any:
    """`value` already has the default's type; enforce finer rules."""
    if path in CHOICES:
        return value if value in CHOICES[path] else default
    if path in RANGES:
        lo, hi = RANGES[path]
        if isinstance(value, float) and not math.isfinite(value):
            return default
        return int(min(hi, max(lo, value)))
    if path == "theme.accent":
        return value if value == "" or _HEX.match(value) else default
    if path == "name":
        return value.strip()[:MAX_NAME]
    if path == "home.widgets":
        ok = [w for w in value if isinstance(w, str) and _WIDGET.match(w)]
        return ok[:MAX_WIDGETS]
    if path == "home.events":
        return _valid_events(value)
    return value


def merged(
    stored: dict | None, defaults: dict = DEFAULTS, _path: str = ""
) -> dict:
    """Deep-merge stored values over defaults. Unknown keys are ignored,
    values of the wrong type fall back to the default, and every value is
    validated."""
    out = copy.deepcopy(defaults)
    if not isinstance(stored, dict):
        return out
    for key, default in defaults.items():
        if key not in stored:
            continue
        path = f"{_path}{key}"
        value = stored[key]
        if isinstance(default, dict):
            out[key] = merged(value, default, path + ".")
            continue
        if isinstance(default, bool):
            ok = isinstance(value, bool)
        elif isinstance(default, (int, float)):
            ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        else:
            ok = isinstance(value, type(default))
        if ok:
            checked = _validate(path, value, default)
            if checked is not None:
                out[key] = checked
    return out


_MISSING = object()


def get_path(data: Any, path: str, default: Any = None) -> Any:
    for part in path.split("."):
        if not isinstance(data, dict) or part not in data:
            return default
        data = data[part]
    return data


def set_path(data: dict, path: str, value: Any) -> dict:
    """Return a copy of data with dotted `path` set to value."""
    out = copy.deepcopy(data)
    node = out
    *parents, leaf = path.split(".")
    for p in parents:
        if not isinstance(node.get(p), dict):
            node[p] = {}
        node = node[p]
    node[leaf] = value
    return out


def diff(data: dict, defaults: dict = DEFAULTS) -> dict:
    """Only the values that differ from the defaults. Storing just these means
    improved defaults in future updates still reach her for everything she
    hasn't customized."""
    out = {}
    for key, default in defaults.items():
        if key not in data:
            continue
        value = data[key]
        if isinstance(default, dict):
            sub = diff(value, default)
            if sub:
                out[key] = sub
        elif value != default:
            out[key] = value
    return out


def unit_for(path: str) -> str | None:
    for unit in UNITS:
        if path == unit or path.startswith(unit + "."):
            return unit
    return None


class Settings:
    """Read/write settings on an open collection."""

    def __init__(self, col):
        self.col = col

    def raw(self) -> dict:
        """Everything stored, including keys this version doesn't know."""
        legacy = self.col.get_config(LEGACY_KEY, None)
        data = copy.deepcopy(legacy) if isinstance(legacy, dict) else {}
        # Least specific first, so "home.events" lands inside "home".
        for unit in reversed(UNITS):
            value = self.col.get_config(PREFIX + unit, None)
            if value is None:
                continue
            if isinstance(value, dict) and isinstance(
                get_path(data, unit), dict
            ):
                value = {**get_path(data, unit), **value}
            data = set_path(data, unit, value)
        return data

    def get(self) -> dict:
        return merged(self.raw())

    def set(self, path: str, value: Any) -> dict:
        unit = unit_for(path)
        if unit is None or get_path(DEFAULTS, path, _MISSING) is _MISSING:
            raise KeyError(path)
        updated = set_path(self.raw(), path, value)
        self._store(unit, updated)
        return self.get()

    def _store(self, unit: str, data: dict) -> None:
        clean = merged(data)
        default = get_path(DEFAULTS, unit)
        value = get_path(clean, unit)
        if isinstance(default, dict):
            stored = diff(value, default)
            # Keep keys a newer version added (and we don't understand).
            raw = get_path(data, unit)
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if k not in default:
                        stored[k] = v
            if unit == "home":
                stored.pop("events", None)  # stored under its own key
        else:
            stored = value if value != default else None
        if stored in (None, {}):
            self.col.remove_config(PREFIX + unit)
        else:
            self.col.set_config(PREFIX + unit, stored)

    def reset(self) -> dict:
        for unit in UNITS:
            self.col.remove_config(PREFIX + unit)
        self.col.remove_config(LEGACY_KEY)
        return self.get()
