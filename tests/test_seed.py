import pytest
from anki.collection import Collection

from devtools.seed import build
from devtools.seed.simulate import simulate

DAYS = 60


@pytest.fixture
def seeded(tmp_path):
    col = Collection(str(tmp_path / "collection.anki2"))
    hard = build(col)
    sim = simulate(col, days=DAYS, seed=1, hard_nids=hard)
    yield col, sim
    col.close()


def test_today_is_after_history(seeded):
    col, sim = seeded
    assert col.sched.today == DAYS
    last_review_day = (max(r[0] for r in sim.revlog) // 1000 - col.crt) // 86400
    assert last_review_day < DAYS


def test_collection_passes_integrity_check(seeded):
    col, _ = seeded
    msg, ok = col.fix_integrity()
    assert ok, msg


def test_history_is_realistic(seeded):
    col, sim = seeded
    assert col.db.scalar("select count() from cards where type = 0") > 0
    assert col.db.scalar("select count() from cards where type = 2") > 0
    retention = col.db.scalar("select avg(ease > 1) from revlog where type=1")
    assert 0.7 < retention < 0.97
    assert sim.leech_nids, "hard notes should produce leeches"
    for nid in sim.leech_nids:
        assert col.get_note(nid).has_tag("leech")


def test_reviews_due_in_seeded_deck(seeded):
    col, _ = seeded
    col.decks.select(col.decks.id("MCAT"))
    assert col.sched.getCard() is not None


def test_refuses_collection_with_history(seeded):
    col, _ = seeded
    with pytest.raises(ValueError):
        simulate(col, days=10)
