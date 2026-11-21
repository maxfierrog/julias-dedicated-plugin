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


def test_deck_progress_counts_today(seeded_col):
    col = seeded_col
    prog = stats.deck_progress(col)
    mcat = col.decks.id("MCAT")
    done, remaining = prog[mcat]
    assert done == 0 and remaining > 0  # seed leaves today unstudied
    col.decks.select(mcat)
    card = col.sched.getCard()
    col.sched.answerCard(card, 3)
    done2, _ = stats.deck_progress(col)[mcat]
    assert done2 == 1


def test_minutes_by_day(seeded_col):
    m = stats.minutes_by_day(seeded_col, 14)
    assert len(m) == 14 and m[-1] == 0
    assert any(x > 0 for x in m)


def test_weak_spots_sorted_by_recall(seeded_col):
    spots = stats.weak_spots(seeded_col, days=90, min_reviews=10)
    assert spots, "seeded history should have reviews"
    assert [w.retention for w in spots] == sorted(w.retention for w in spots)
    assert all("::" in w.name or w.name for w in spots)


def test_backlog_plan(seeded_col):
    b = stats.backlog(seeded_col)
    assert b.overdue > 0  # the seed skips the last two days
    assert b.extra_per_day >= 10
    assert b.days_to_clear * b.extra_per_day >= b.overdue


def test_finish_lines(seeded_col):
    lines = stats.finish_lines(seeded_col)
    names = {f.name for f in lines}
    assert "MCAT" in names
    mcat = next(f for f in lines if f.name == "MCAT")
    assert mcat.unseen > 0 and mcat.per_day > 0 and mcat.days_left > 0


def test_new_card_cost(seeded_col):
    cost = stats.new_card_cost(seeded_col)
    assert cost is not None
    assert 2 < cost.reviews_first_month < 15
    assert cost.minutes_per_day(20) > 0
