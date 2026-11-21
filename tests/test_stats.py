import pytest

from conftest import load_addon_module

stats = load_addon_module("stats")


def test_pace_reflects_history(seeded_col):
    p = stats.pace(seeded_col)
    assert 3 < p.seconds_per_answer < 30
    assert 1.5 < p.answers_per_new < 6
    assert 1.0 <= p.answers_per_review < 1.5
    assert p.estimate(0, 0, 0) == 0
    assert p.estimate(10, 0, 0) > p.estimate(0, 0, 10)


def test_pace_defaults_without_history(tmp_path):
    from anki.collection import Collection

    col = Collection(str(tmp_path / "empty.anki2"))
    try:
        p = stats.pace(col)
        assert p.seconds_per_answer == stats.DEFAULT_SECONDS_PER_ANSWER
        assert p.answers_per_new == stats.DEFAULT_ANSWERS_PER_NEW
    finally:
        col.close()


def test_queue_counts_match_scheduler(seeded_col):
    new, learn, review = stats.queue_counts(seeded_col)
    assert review > 0 and new > 0
    tree = seeded_col.sched.deck_due_tree()
    assert review == sum(n.review_count for n in tree.children)


def test_forecast_today_includes_overdue(seeded_col):
    f = stats.forecast(seeded_col, days=7)
    assert len(f) == 7
    overdue_or_today = seeded_col.db.scalar(
        "select count() from cards where queue in (2,3) and due <= ?",
        seeded_col.sched.today,
    )
    assert f[0] == overdue_or_today
    assert sum(f[1:]) > 0


def test_retention_in_range(seeded_col):
    r = stats.retention(seeded_col)
    assert r.reviews > 0
    assert 0.6 < r.overall < 1.0


def test_history_and_streak(seeded_col):
    counts = stats.daily_counts(seeded_col, 90)
    assert len(counts) == 90
    assert counts[-1] == 0  # the seed leaves today unstudied
    assert counts[-2] == 0 and counts[-3] == 0  # and skips the two days before
    s = stats.streak(seeded_col)
    assert s.studied_today is False
    assert s.current == 0
    assert s.longest >= 3


@pytest.mark.parametrize(
    "seconds, text",
    [
        (20, "under a minute"),
        (60 * 14, "14 min"),
        (3600, "1 h"),
        (5400, "1 h 30 min"),
    ],
)
def test_format_minutes(seconds, text):
    assert stats.format_minutes(seconds) == text
