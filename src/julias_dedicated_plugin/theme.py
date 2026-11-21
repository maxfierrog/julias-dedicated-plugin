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
    sun: str  # warm highlight for playful touches (streaks, doodles)


@dataclass(frozen=True)
class Preset:
    name: str
    light: Palette
    dark: Palette


PRESETS: dict[str, Preset] = {
    # Soft periwinkle with a warm sunny highlight: the default.
    "periwinkle": Preset(
        "Periwinkle",
        Palette(
            "#F6F7FE",
            "#FFFFFF",
            "#ECEEFB",
            "#1E2040",
            "#63668A",
            "#A2A5C4",
            "#DDE0F5",
            "#E8EAF9",
            "#6C7FE0",
            "#6C7FE0",
            "#E0617A",
            "#4FA37A",
            "#F2B84B",
        ),
        Palette(
            "#16172A",
            "#1F2136",
            "#121322",
            "#E8E9F8",
            "#A2A5C6",
            "#6B6E92",
            "#303352",
            "#272A44",
            "#9DABF5",
            "#9DABF5",
            "#F28DA0",
            "#86D1AA",
            "#FFCF6B",
        ),
    ),
    # Warm cream and plum, tangerine accent.
    "peach": Preset(
        "Peach",
        Palette(
            "#FFF8F1",
            "#FFFFFF",
            "#FCEEE2",
            "#2B1631",
            "#7A6373",
            "#B5A3AE",
            "#F1DFD3",
            "#F7E9DF",
            "#E8613A",
            "#4C8FD6",
            "#E0533D",
            "#5FA866",
            "#F4B23E",
        ),
        Palette(
            "#1F1620",
            "#2A1F2B",
            "#191219",
            "#F6EBEF",
            "#B9A6B3",
            "#7C6A78",
            "#3E3140",
            "#332735",
            "#FF8A63",
            "#86B8F0",
            "#FF8670",
            "#8FD196",
            "#FFC960",
        ),
    ),
    "matcha": Preset(
        "Matcha",
        Palette(
            "#F6FAF1",
            "#FFFFFF",
            "#EAF3E2",
            "#1D2B1F",
            "#64755F",
            "#A2B19C",
            "#DCE8D3",
            "#E7F0E0",
            "#4E9A5B",
            "#4D86C9",
            "#D9634C",
            "#4E9A5B",
            "#E9B949",
        ),
        Palette(
            "#151C16",
            "#1D261F",
            "#111712",
            "#E7F1E5",
            "#9DB39A",
            "#677A65",
            "#2D3A2F",
            "#253027",
            "#8FD197",
            "#8DBCEB",
            "#F09A86",
            "#8FD197",
            "#F2CE6B",
        ),
    ),
    "berry": Preset(
        "Berry",
        Palette(
            "#FDF6FA",
            "#FFFFFF",
            "#F8E8F1",
            "#2E1428",
            "#7D6176",
            "#B9A1B3",
            "#F0DCE8",
            "#F6E7EF",
            "#C94F8B",
            "#7C6BD6",
            "#E0533D",
            "#4F9E78",
            "#F2B347",
        ),
        Palette(
            "#1D141B",
            "#281C25",
            "#171016",
            "#F6E9F1",
            "#BBA2B4",
            "#7E6679",
            "#3E2E3A",
            "#332631",
            "#F28DBC",
            "#B3A7F5",
            "#FF8670",
            "#86CFA8",
            "#FFCA6A",
        ),
    ),
    "sky": Preset(
        "Sky",
        Palette(
            "#F4F8FD",
            "#FFFFFF",
            "#E7F0FA",
            "#14243A",
            "#5C6F86",
            "#9DAEC2",
            "#D8E4F2",
            "#E4EDF7",
            "#3D7FD9",
            "#3D7FD9",
            "#E0603F",
            "#3E9C72",
            "#F2B23E",
        ),
        Palette(
            "#121925",
            "#1A2331",
            "#0E141E",
            "#E6EEF8",
            "#97A9C0",
            "#62738B",
            "#2A374A",
            "#222D3D",
            "#7FB2F5",
            "#7FB2F5",
            "#FF8F70",
            "#7ED3AA",
            "#FFCB63",
        ),
    ),
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
            "#D9A441",
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
            "#E8C26E",
        ),
    ),
}

DISPLAY_FONT = (
    '"Quicksand Variable", "Nunito Variable", -apple-system, sans-serif'
)

UI_FONTS = {
    "rounded": '"Nunito Variable", "Inter Variable", -apple-system, sans-serif',
    "inter": '"Inter Variable", -apple-system, "Segoe UI", sans-serif',
    "system": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
}

CARD_FONTS = {
    "nunito": '"Nunito Variable", "Inter Variable", -apple-system, sans-serif',
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
        "--jdp-sun": p.sun,
        "--jdp-shadow": shadow,
    }
    if anki:
        pairs = {**anki_pairs, **pairs}
    return "".join(f"{k}:{v};" for k, v in pairs.items())


def tokens_css(settings: dict) -> str:
    """CSS defining every theme token for light and dark mode."""
    t, c = settings["theme"], settings["cards"]
    preset = PRESETS.get(t["preset"], PRESETS["periwinkle"])
    custom = t["accent"] if valid_hex(t["accent"]) else ""
    light_accent = custom or preset.light.accent
    # A custom accent is lifted toward white in dark mode to stay legible.
    dark_accent = (
        f"color-mix(in oklab, {custom} 72%, white)"
        if custom
        else preset.dark.accent
    )
    anki = settings["modules"]["theme"]
    radius = max(0, min(28, int(t["radius"])))
    shared = "".join(
        f"{k}:{v};"
        for k, v in {
            "--jdp-font-ui": UI_FONTS.get(t["ui_font"], UI_FONTS["rounded"]),
            "--jdp-font-display": DISPLAY_FONT,
            "--jdp-bounce": "cubic-bezier(0.34, 1.56, 0.64, 1)",
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


def canvas_color(settings: dict, dark: bool) -> str:
    preset = PRESETS.get(settings["theme"]["preset"], PRESETS["periwinkle"])
    return (preset.dark if dark else preset.light).canvas
