"""Theme presets and the CSS custom properties generated from settings.

We drive Anki's own design tokens (--canvas, --fg, --border, ...), so every
stock web screen follows the theme, and add our own (--jdp-*) for our UI and
card styling. Every preset has a light and a dark palette; which one applies
follows Anki's own night mode (`:root.night-mode`).
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    canvas: str
    elevated: str
    inset: str
    fg: str
    subtle: str
    faint: str
    border: str
    border_subtle: str
    accent: str
    new: str
    learn: str
    review: str


@dataclass(frozen=True)
class Preset:
    name: str
    light: Palette
    dark: Palette


PRESETS: dict[str, Preset] = {
    "paper": Preset(
        "Paper",
        Palette(
            "#F6F3EE",
            "#FFFDF9",
            "#EFEBE4",
            "#26231F",
            "#736C62",
            "#A39B90",
            "#E2DCD2",
            "#ECE7DF",
            "#2F5DA8",
            "#2F5DA8",
            "#C2543D",
            "#4E8A5A",
        ),
        Palette(
            "#1D1B18",
            "#262320",
            "#171512",
            "#ECE7DF",
            "#A0988C",
            "#6E675E",
            "#36322D",
            "#2D2A26",
            "#8FB0EA",
            "#8FB0EA",
            "#E58C76",
            "#8CC49A",
        ),
    ),
    "sage": Preset(
        "Sage",
        Palette(
            "#F2F4EF",
            "#FCFDFB",
            "#E9ECE5",
            "#1F2620",
            "#66705F",
            "#9AA393",
            "#DDE2D7",
            "#E7EBE2",
            "#4C7A57",
            "#4F78A8",
            "#C0604A",
            "#4C7A57",
        ),
        Palette(
            "#161A17",
            "#1E2420",
            "#121512",
            "#E2E8E1",
            "#98A394",
            "#66705F",
            "#2E362F",
            "#252B26",
            "#86B892",
            "#8DB2DD",
            "#E39580",
            "#86B892",
        ),
    ),
    "lilac": Preset(
        "Lilac",
        Palette(
            "#F5F3F9",
            "#FEFDFF",
            "#ECE9F3",
            "#24212E",
            "#6E6880",
            "#A19BB3",
            "#E0DCEA",
            "#EAE7F1",
            "#6A55C9",
            "#6A55C9",
            "#C25563",
            "#3F8A6B",
        ),
        Palette(
            "#18161F",
            "#211E2A",
            "#13121A",
            "#E9E6F2",
            "#9F98B3",
            "#6C6680",
            "#322E3E",
            "#282533",
            "#A898F2",
            "#A898F2",
            "#EE8E9A",
            "#7CC4A3",
        ),
    ),
    "slate": Preset(
        "Slate",
        Palette(
            "#F1F4F7",
            "#FFFFFF",
            "#E7ECF1",
            "#1B2430",
            "#5F6B7A",
            "#97A2AF",
            "#D9E0E8",
            "#E5EAF0",
            "#2F6FB5",
            "#2F6FB5",
            "#C4513F",
            "#3D8B63",
        ),
        Palette(
            "#12161B",
            "#1A2027",
            "#0E1115",
            "#E4E9EF",
            "#93A0AE",
            "#5F6B7A",
            "#29313B",
            "#212830",
            "#6FA8EA",
            "#6FA8EA",
            "#EE8A78",
            "#74C29A",
        ),
    ),
}

UI_FONTS = {
    "inter": '"Inter Variable", -apple-system, "Segoe UI", sans-serif',
    "system": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
}

CARD_FONTS = {
    "atkinson": '"Atkinson Hyperlegible", "Inter Variable", -apple-system, sans-serif',
    "literata": '"Literata Variable", Georgia, "Times New Roman", serif',
    "inter": '"Inter Variable", -apple-system, "Segoe UI", sans-serif',
    "system": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
}

CARD_WIDTHS = {"narrow": "38rem", "medium": "46rem", "wide": "60rem"}
DENSITY_SPACE = {"compact": "0.75", "comfortable": "1"}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def valid_hex(value: str) -> bool:
    return bool(_HEX.match(value or ""))


def _on_accent(hex_color: str) -> str:
    """Readable text color on top of an accent (WCAG relative luminance)."""
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))

    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return "#16130F" if lum > 0.36 else "#FFFFFF"


def _palette_vars(
    p: Palette, accent: str, dark: bool, on_accent: str, anki: bool
) -> str:
    shadow = (
        "0 1px 2px rgb(0 0 0 / 0.25), 0 4px 16px rgb(0 0 0 / 0.25)"
        if dark
        else ("0 1px 2px rgb(40 30 20 / 0.06), 0 6px 20px rgb(40 30 20 / 0.06)")
    )
    anki_pairs = {
        "--fg": p.fg,
        "--fg-subtle": p.subtle,
        "--fg-disabled": p.faint,
        "--fg-faint": p.faint,
        "--fg-link": accent,
        "--canvas": p.canvas,
        "--canvas-elevated": p.elevated,
        "--canvas-inset": p.inset,
        "--canvas-overlay": p.elevated,
        "--canvas-code": p.inset,
        "--border": p.border,
        "--border-subtle": p.border_subtle,
        "--border-strong": p.subtle,
        "--border-focus": accent,
        "--button-bg": p.elevated,
        "--button-gradient-start": p.elevated,
        "--button-gradient-end": p.elevated,
        "--button-hover-border": p.subtle,
        "--button-primary-bg": accent,
        "--button-primary-gradient-start": accent,
        "--button-primary-gradient-end": accent,
        "--scrollbar-bg": p.border,
        "--scrollbar-bg-hover": p.faint,
        "--scrollbar-bg-active": p.subtle,
        "--shadow": p.border,
        "--shadow-focus": accent,
        "--focus-color": accent,
        "--state-new": p.new,
        "--state-learn": p.learn,
        "--state-review": p.review,
        "--highlight-bg": f"color-mix(in srgb, {accent} 30%, transparent)",
        "--selected-bg": f"color-mix(in srgb, {accent} 18%, transparent)",
    }
    pairs = {
        "--jdp-canvas": p.canvas,
        "--jdp-elevated": p.elevated,
        "--jdp-inset": p.inset,
        "--jdp-fg": p.fg,
        "--jdp-subtle": p.subtle,
        "--jdp-faint": p.faint,
        "--jdp-border": p.border,
        "--jdp-border-subtle": p.border_subtle,
        "--jdp-accent": accent,
        "--jdp-on-accent": on_accent,
        "--jdp-accent-soft": f"color-mix(in srgb, {accent} 14%, transparent)",
        "--jdp-accent-line": f"color-mix(in srgb, {accent} 45%, transparent)",
        "--jdp-new": p.new,
        "--jdp-learn": p.learn,
        "--jdp-review": p.review,
        "--jdp-shadow": shadow,
    }
    if anki:
        pairs = {**anki_pairs, **pairs}
    return "".join(f"{k}:{v};" for k, v in pairs.items())


def tokens_css(settings: dict) -> str:
    """CSS defining every theme token for light and dark mode."""
    t, c = settings["theme"], settings["cards"]
    preset = PRESETS.get(t["preset"], PRESETS["paper"])
    custom = t["accent"] if valid_hex(t["accent"]) else ""
    light_accent = custom or preset.light.accent
    # A custom accent is lifted toward white in dark mode to stay legible.
    dark_accent = (
        f"color-mix(in oklab, {custom} 72%, white)"
        if custom
        else preset.dark.accent
    )
    anki = settings["modules"]["theme"]
    radius = max(0, min(24, int(t["radius"])))
    shared = "".join(
        f"{k}:{v};"
        for k, v in {
            "--jdp-font-ui": UI_FONTS.get(t["ui_font"], UI_FONTS["inter"]),
            "--jdp-font-card": CARD_FONTS.get(
                c["font"], CARD_FONTS["atkinson"]
            ),
            "--jdp-card-size": f"{max(14, min(36, int(c['size'])))}px",
            "--jdp-card-width": CARD_WIDTHS.get(
                c["width"], CARD_WIDTHS["medium"]
            ),
            "--jdp-radius": f"{radius}px",
            "--jdp-radius-sm": f"{max(0, radius - 4)}px",
            "--jdp-space": DENSITY_SPACE.get(t["density"], "1"),
        }.items()
    )
    light_vars = _palette_vars(
        preset.light, light_accent, False, _on_accent(light_accent), anki
    )
    # A lifted custom accent is a color-mix() expression we can't measure;
    # it is always light enough that dark text reads best on it.
    dark_on = "#16130F" if custom else _on_accent(preset.dark.accent)
    dark_vars = _palette_vars(preset.dark, dark_accent, True, dark_on, anki)
    return f":root{{{shared}{light_vars}}}:root.night-mode{{{dark_vars}}}"


def html_classes(settings: dict) -> list[str]:
    """Classes for <html> (body classes are reset by Anki on every card)."""
    m, c, t = settings["modules"], settings["cards"], settings["theme"]
    classes = ["jdp", f"jdp-density-{t['density']}"]
    if m["session"]:
        classes.append("jdp-session")
    if m["cards"]:
        classes += [
            "jdp-cards",
            f"jdp-align-{c['align']}",
            f"jdp-surface-{c['surface']}",
            f"jdp-dark-images-{c['dark_images']}",
        ]
        if c["override_colors"]:
            classes.append("jdp-card-colors")
    return classes
