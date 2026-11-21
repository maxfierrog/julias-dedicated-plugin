"""Theme Anki's native (Qt) windows: Browse, Add, Edit, dialogs, Preferences.

Restrained on purpose: these windows are functional, so we only feed our
palette into Anki's own design tokens (aqt.colors) and let Anki's existing
Qt palette and stylesheet do the rest. Same widgets, same layout, same
fonts; just our colors. Original values are kept so it can be undone.
"""

import aqt.colors as colors
from aqt import mw
from aqt.theme import theme_manager

from . import theme

_originals: dict[str, dict] = {}


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


def _mapping(p: theme.Palette, accent: str) -> dict[str, str]:
    return {
        "FG": p.fg,
        "FG_SUBTLE": p.subtle,
        "FG_DISABLED": p.faint,
        "FG_FAINT": p.faint,
        "FG_LINK": accent,
        "CANVAS": p.canvas,
        "CANVAS_ELEVATED": p.elevated,
        "CANVAS_INSET": p.inset,
        "CANVAS_OVERLAY": p.elevated,
        "CANVAS_CODE": p.elevated,
        "BORDER": p.border,
        "BORDER_SUBTLE": p.border_subtle,
        "BORDER_STRONG": p.subtle,
        "BORDER_FOCUS": accent,
        "BUTTON_BG": p.elevated,
        "BUTTON_GRADIENT_START": p.elevated,
        "BUTTON_GRADIENT_END": p.elevated,
        "BUTTON_HOVER_BORDER": p.subtle,
        "BUTTON_PRIMARY_BG": accent,
        "BUTTON_PRIMARY_GRADIENT_START": accent,
        "BUTTON_PRIMARY_GRADIENT_END": accent,
        "SCROLLBAR_BG": p.border,
        "SCROLLBAR_BG_HOVER": p.faint,
        "SCROLLBAR_BG_ACTIVE": p.subtle,
        "HIGHLIGHT_BG": _rgba(accent, 0.35),
        "SELECTED_BG": _rgba(accent, 0.22),
        "STATE_NEW": p.new,
        "STATE_LEARN": p.learn,
        "STATE_REVIEW": p.review,
    }


def apply(settings: dict) -> None:
    """Point Anki's tokens at our palette (or restore them), then re-style."""
    preset = theme.PRESETS.get(
        settings["theme"]["preset"], theme.PRESETS["periwinkle"]
    )
    custom = (
        settings["theme"]["accent"]
        if theme.valid_hex(settings["theme"]["accent"])
        else ""
    )
    on = settings["modules"]["theme"]
    light = _mapping(preset.light, custom or preset.light.accent)
    dark = _mapping(preset.dark, custom or preset.dark.accent)
    for name in light:
        token = getattr(colors, name, None)
        if not isinstance(token, dict):
            continue
        _originals.setdefault(
            name, {"light": token["light"], "dark": token["dark"]}
        )
        if on:
            token["light"], token["dark"] = light[name], dark[name]
        else:
            token.update(_originals[name])
    # Force Anki to rebuild its Qt palette + stylesheet from the tokens.
    theme_manager._current_widget_style = None
    theme_manager.apply_style()
    mw.update()
