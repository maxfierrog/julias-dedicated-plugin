import sys
import types

from conftest import ADDON, load_addon_module


def _briefing():
    # briefing.py does `from . import stats`; load it inside a stub package.
    import importlib.util

    stats = load_addon_module("stats")
    pkg = types.ModuleType("jdp_b")
    pkg.__path__ = [str(ADDON)]
    sys.modules["jdp_b"] = pkg
    sys.modules["jdp_b.stats"] = stats
    spec = importlib.util.spec_from_file_location(
        "jdp_b.briefing", ADDON / "briefing.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["jdp_b.briefing"] = mod
    spec.loader.exec_module(mod)
    return mod


briefing = _briefing()
settings = load_addon_module("settings")


def test_home_renders_all_sections(seeded_col):
    html = briefing.home_html(seeded_col, settings.merged(None))
    for part in (
        "jdp-hello",
        "jdp-cta",
        "Coming up",
        "Memory",
        "Streak",
        "jdp-heatmap",
    ):
        assert part in html
    assert "done so far" not in html


def test_deck_progress_script_only_for_started_decks(seeded_col):
    assert "{}" in briefing.deck_progress_script(seeded_col)  # nothing yet
    col = seeded_col
    col.decks.select(col.decks.id("MCAT"))
    col.sched.answerCard(col.sched.getCard(), 3)
    script = briefing.deck_progress_script(col)
    assert str(col.decks.id("MCAT")) in script
    assert script.count("<script>") == 1 and script.endswith("</script>")


def test_every_widget_renders_at_every_size(seeded_col):
    cfg = settings.merged(
        {"home": {"events": [{"title": "MCAT", "date": "2099-01-01"}]}}
    )
    for wid, (name, _desc, sizes, render) in briefing.WIDGETS.items():
        for cols, rows in sizes:
            out = render(seeded_col, cfg, cols, rows)
            assert "jdp-tile" in out, (wid, cols, rows)
        html = briefing._widget(wid, sizes[0], seeded_col, cfg)
        assert "Couldn't load" not in html, wid


def test_layout_entries_parse_and_fall_back():
    assert briefing.parse_entry("forecast:3x1") == ("forecast", (3, 1))
    assert briefing.parse_entry("forecast:9x9") == ("forecast", (2, 1))
    assert briefing.parse_entry("streak") == ("streak", (1, 1))
    assert briefing.parse_entry("nope") is None


def test_timeline_event_links_to_its_deck(seeded_col):
    mcat = seeded_col.decks.id("MCAT")
    cfg = settings.merged(
        {
            "home": {
                "events": [
                    {"title": "MCAT", "date": "2099-01-01", "deck": mcat},
                    {"title": "Party", "date": "2099-02-01"},
                ]
            }
        }
    )
    out = briefing._w_timeline(seeded_col, cfg, 3, 1)
    assert f"jdp:study:{mcat}" in out
    assert out.count("jdp-tl-linked") == 1  # only the event with a deck
    assert "<select name='deck'" in out
