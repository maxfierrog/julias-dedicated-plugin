import pytest
from anki.collection import Collection

from conftest import load_addon_module

settings = load_addon_module("settings")


@pytest.fixture
def col(tmp_path):
    c = Collection(str(tmp_path / "c.anki2"))
    yield c
    c.close()


def test_choices_ranges_and_markup_are_rejected():
    m = settings.merged(
        {
            "theme": {
                "density": "x</script><script>",
                "radius": 1e9,
                "preset": "nope",
                "accent": "red;}",
            },
            "cards": {"size": -5, "align": "left right"},
            "home": {
                "goal_minutes": float("inf"),
                "widgets": ["streak", "bad id!"],
            },
            "name": "  J " + "x" * 100,
        }
    )
    assert m["theme"]["density"] == "comfortable"
    assert m["theme"]["radius"] == 28 and m["cards"]["size"] == 14
    assert m["theme"]["preset"] == "periwinkle" and m["theme"]["accent"] == ""
    assert m["cards"]["align"] == "auto"
    assert m["home"]["goal_minutes"] == 30
    assert m["home"]["widgets"] == ["streak"]
    assert len(m["name"]) == settings.MAX_NAME and m["name"].startswith("J")


def test_events_are_cleaned():
    m = settings.merged(
        {
            "home": {
                "events": [
                    "x",
                    {"title": "a"},
                    {"title": " MCAT ", "date": "2027-02-17", "deck": 5},
                    {"title": "", "date": "2027-01-01"},
                ]
            }
        }
    )
    assert m["home"]["events"] == [
        {"title": "MCAT", "date": "2027-02-17", "deck": 5}
    ]


def test_sections_are_stored_separately(col):
    s = settings.Settings(col)
    s.set("theme.preset", "sage" if False else "matcha")
    s.set("home.events", [{"title": "MCAT", "date": "2027-02-17"}])
    s.set("home.widgets", ["streak"])
    assert col.get_config("jdp.theme") == {"preset": "matcha"}
    assert col.get_config("jdp.home.events")[0]["title"] == "MCAT"
    assert "events" not in col.get_config("jdp.home")
    got = s.get()
    assert got["theme"]["preset"] == "matcha"
    assert got["home"]["widgets"] == ["streak"]
    assert got["home"]["events"][0]["date"] == "2027-02-17"


def test_unknown_keys_from_newer_versions_survive(col):
    col.set_config("jdp.theme", {"preset": "berry", "sparkles": "on"})
    settings.Settings(col).set("theme.radius", 10)
    stored = col.get_config("jdp.theme")
    assert stored["sparkles"] == "on" and stored["radius"] == 10


def test_legacy_single_key_is_read_and_migrated(col):
    col.set_config(
        "jdp_settings", {"name": "Jules", "theme": {"preset": "sky"}}
    )
    s = settings.Settings(col)
    assert s.get()["name"] == "Jules" and s.get()["theme"]["preset"] == "sky"
    s.set("theme.radius", 4)
    assert s.get()["theme"]["preset"] == "sky"  # untouched legacy value kept


def test_default_values_remove_the_key_and_reset_clears_all(col):
    s = settings.Settings(col)
    s.set("cards.size", 26)
    s.set("cards.size", 22)  # back to default
    assert col.get_config("jdp.cards", None) is None
    s.set("name", "Jo")
    assert s.reset() == settings.DEFAULTS
    assert col.get_config("jdp.name", None) is None


def test_unknown_paths_rejected(col):
    with pytest.raises(KeyError):
        settings.Settings(col).set("theme.nope", 1)
    with pytest.raises(KeyError):
        settings.Settings(col).set("bogus", 1)
