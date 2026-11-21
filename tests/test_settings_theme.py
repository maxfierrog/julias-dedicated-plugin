import re

from conftest import load_addon_module

settings = load_addon_module("settings")
theme = load_addon_module("theme")


def test_merged_fills_defaults_and_drops_bad_values():
    stored = {
        "name": "J",
        "theme": {"preset": "sage", "radius": "big"},  # bad type ignored
        "modules": {"fatigue": 1},  # int is not a bool
        "unknown": 5,
    }
    m = settings.merged(stored)
    assert m["name"] == "J"
    assert m["theme"]["preset"] == "sage"
    assert m["theme"]["radius"] == settings.DEFAULTS["theme"]["radius"]
    assert m["modules"]["fatigue"] is False
    assert "unknown" not in m
    assert m["cards"] == settings.DEFAULTS["cards"]


def test_settings_roundtrip_in_collection(tmp_path):
    from anki.collection import Collection

    col = Collection(str(tmp_path / "c.anki2"))
    try:
        store = settings.Settings(col)
        assert store.get() == settings.DEFAULTS
        store.set("cards.size", 26)
        store.set("modules.fatigue", True)
        again = settings.Settings(col).get()
        assert again["cards"]["size"] == 26
        assert again["modules"]["fatigue"] is True
        assert store.reset() == settings.DEFAULTS
    finally:
        col.close()


def _vars(css, scope):
    block = re.search(re.escape(scope) + r"\{([^}]*)\}", css).group(1)
    return dict(kv.split(":", 1) for kv in block.split(";") if kv)


def test_tokens_cover_light_and_dark_for_every_preset():
    for key in theme.PRESETS:
        s = settings.merged({"theme": {"preset": key}})
        css = theme.tokens_css(s)
        light = _vars(css, ":root")
        dark = _vars(css, ":root.night-mode")
        for v in ("--fg", "--canvas", "--jdp-accent", "--jdp-on-accent"):
            assert v in light and v in dark
        assert light["--canvas"] != dark["--canvas"]


def test_custom_accent_applies_without_touching_state_colors():
    s = settings.merged({"theme": {"preset": "paper", "accent": "#B4436C"}})
    css = theme.tokens_css(s)
    light = _vars(css, ":root")
    dark = _vars(css, ":root.night-mode")
    assert light["--jdp-accent"] == "#B4436C"
    assert "#B4436C" in dark["--jdp-accent"]  # lifted via color-mix
    # Paper's dark "new" color equals its dark accent; it must not change.
    assert dark["--jdp-new"] == theme.PRESETS["paper"].dark.new


def test_invalid_accent_falls_back_to_preset():
    s = settings.merged({"theme": {"accent": "red; }"}})
    light = _vars(theme.tokens_css(s), ":root")
    default = settings.DEFAULTS["theme"]["preset"]
    assert light["--jdp-accent"] == theme.PRESETS[default].light.accent


def test_theme_module_off_leaves_anki_tokens_alone():
    s = settings.merged({"modules": {"theme": False}})
    light = _vars(theme.tokens_css(s), ":root")
    assert "--fg" not in light and "--jdp-fg" in light


def test_on_accent_contrast():
    assert theme._on_accent("#FFFFFF") != "#FFFFFF"
    assert theme._on_accent("#2F5DA8") == "#FFFFFF"
