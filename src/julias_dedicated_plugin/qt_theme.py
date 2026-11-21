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
_registered: set[str] = set()


def _qt_family(settings: dict) -> str | None:
    """Her interface font as a Qt family, registering it on first use."""
    import os

    from aqt.qt import QFontDatabase

    family = theme.QT_FONT_FAMILIES.get(settings["theme"]["ui_font"])
    if family and family not in _registered:
        path = os.path.join(
            os.path.dirname(__file__),
            "web",
            "fonts",
            "ttf",
            theme.QT_FONT_FILES[family],
        )
        if QFontDatabase.addApplicationFont(path) < 0:
            return None
        _registered.add(family)
    return family


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


def _mapping(p: theme.Palette, accent: str, primary: str) -> dict[str, str]:
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
        # Anki draws white text on primary buttons, so these always use the
        # deeper (light-mode) accent for contrast.
        "BUTTON_PRIMARY_BG": primary,
        "BUTTON_PRIMARY_GRADIENT_START": primary,
        "BUTTON_PRIMARY_GRADIENT_END": primary,
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
    primary = custom or preset.light.accent
    light = _mapping(preset.light, custom or preset.light.accent, primary)
    dark = _mapping(preset.dark, custom or preset.dark.accent, primary)
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


def qss(settings: dict, dark: bool) -> str:
    """A light-touch Qt stylesheet for functional windows: our shapes and
    accent on inputs, buttons, menus, lists and headers. System font and
    density are kept; nothing bounces or shouts."""
    preset = theme.PRESETS.get(
        settings["theme"]["preset"], theme.PRESETS["periwinkle"]
    )
    p = preset.dark if dark else preset.light
    custom = settings["theme"]["accent"]
    accent = custom if theme.valid_hex(custom) else p.accent
    soft = _rgba(accent, 0.18)
    # Follows the corner setting (0 = square), a little tighter than the
    # main screens since these controls are small and dense.
    r = round(int(settings["theme"]["radius"]) * 0.6)
    family = _qt_family(settings)
    font = f'QWidget {{ font-family: "{family}"; }}' if family else ""
    return font + f"""
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QPlainTextEdit,
QTextEdit {{
    border: 1px solid {p.border};
    border-radius: {r}px;
    padding: 3px 7px;
    background: {p.elevated};
    selection-background-color: {_rgba(accent, 0.35)};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {accent};
}}
QPushButton {{
    border: 1px solid {p.border};
    border-radius: {r}px;
    padding: 4px 12px;
    background: {p.elevated};
}}
QPushButton:hover {{
    border-color: {p.subtle};
}}
QPushButton:default, QPushButton:checked {{
    border-color: {accent};
}}
QPushButton:focus {{
    border-color: {accent};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {accent};
    border: 1px solid {accent};
}}
QHeaderView::section {{
    background: {p.canvas};
    color: {p.subtle};
    font-weight: 600;
    border: none;
    border-bottom: 1px solid {p.border_subtle};
    padding: 4px 6px;
}}
QTableView {{
    gridline-color: {p.border_subtle};
    selection-background-color: {soft};
    selection-color: {p.fg};
}}
QTreeView::item {{
    padding: 2px 0;
}}
QTreeView::item:selected, QListView::item:selected {{
    background: {soft};
    color: {p.fg};
    border-radius: {r}px;
}}
QMenu {{
    background: {p.elevated};
    border: 1px solid {p.border};
    border-radius: {r + 2}px;
    padding: 4px;
}}
QMenu::item {{
    padding: 4px 18px 4px 10px;
    border-radius: {r}px;
    /* Anki uses margin-bottom only, which leaves extra space under the
       last item; split it so top and bottom edges match. */
    margin: 2px 0;
}}
QMenu::item:selected {{
    background: {soft};
    color: {p.fg};
}}
QMenu::separator {{
    height: 1px;
    background: {p.border_subtle};
    margin: 4px 6px;
}}
QToolTip {{
    background: {p.elevated};
    color: {p.fg};
    border: 1px solid {p.border};
    border-radius: {r}px;
    padding: 4px 6px;
}}
QScrollBar:vertical {{
    width: 10px;
    background: transparent;
}}
QScrollBar:horizontal {{
    height: 10px;
    background: transparent;
}}
QScrollBar::handle {{
    background: {p.border};
    border-radius: 4px;
    margin: 2px;
}}
QScrollBar::handle:hover {{
    background: {p.faint};
}}
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
    width: 0;
    height: 0;
}}
"""


def on_style_did_init(buf: str) -> str:
    from .web import settings

    s = settings()
    if not s["modules"]["theme"] or mw.col is None:
        return buf
    return buf + qss(s, theme_manager.night_mode)
