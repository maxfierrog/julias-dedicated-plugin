"""User settings, stored in the collection config so they sync via AnkiWeb
and follow her between computers. Missing keys fall back to DEFAULTS, so new
settings added in updates appear automatically.
"""

import copy
from typing import Any

CONFIG_KEY = "jdp_settings"

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
        "forecast": True,
        "heatmap": True,
        "retention": True,
    },
}


def merged(stored: dict | None, defaults: dict = DEFAULTS) -> dict:
    """Deep-merge stored values over defaults, ignoring unknown keys and
    values whose type doesn't match the default."""
    out = copy.deepcopy(defaults)
    if not isinstance(stored, dict):
        return out
    for key, default in defaults.items():
        if key not in stored:
            continue
        value = stored[key]
        if isinstance(default, dict):
            out[key] = merged(value, default)
        elif isinstance(default, bool):
            if isinstance(value, bool):
                out[key] = value
        elif isinstance(default, (int, float)):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out[key] = value
        elif isinstance(value, type(default)):
            out[key] = value
    return out


def set_path(data: dict, path: str, value: Any) -> dict:
    """Return a copy of data with dotted `path` set to value."""
    out = copy.deepcopy(data)
    node = out
    *parents, leaf = path.split(".")
    for p in parents:
        node = node.setdefault(p, {})
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


class Settings:
    """Read/write settings on an open collection."""

    def __init__(self, col):
        self.col = col

    def get(self) -> dict:
        return merged(self.col.get_config(CONFIG_KEY, None))

    def set(self, path: str, value: Any) -> dict:
        updated = merged(set_path(self.get(), path, value))
        self.col.set_config(CONFIG_KEY, diff(updated))
        return updated

    def reset(self) -> dict:
        self.col.set_config(CONFIG_KEY, {})
        return self.get()
