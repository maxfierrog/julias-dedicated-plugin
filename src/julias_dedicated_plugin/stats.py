"""Study statistics computed from the collection (no GUI imports, so this is
unit-tested against a seeded collection).

Day boundaries follow Anki's: a day starts at the "next day starts at" hour
(`col.sched.day_cutoff` is the end of today).
"""

import contextlib
from dataclasses import dataclass

# Within one home-screen render, expensive shared inputs are computed once.
_cache: dict | None = None


@contextlib.contextmanager
def render_cache():
    global _cache
    _cache = {}
    try:
        yield
    finally:
        _cache = None


def _cached(key, compute):
    if _cache is None:
        return compute()
    if key not in _cache:
        _cache[key] = compute()
    return _cache[key]


def due_tree(col):
    return _cached("due_tree", col.sched.deck_due_tree)


DAY = 86_400
# Revlog rows that are real answers (not Forget/Set due date/reschedule rows,
# which have type >= 4 and ease 0).
ANSWER = "type in (0, 1, 2, 3) and ease > 0"
DEFAULT_SECONDS_PER_ANSWER = 10.0
DEFAULT_ANSWERS_PER_NEW = 2.5
MAX_ANSWER_SECONDS = 60.0


def _day_start(col, days_ago: int = 0) -> int:
    return col.sched.day_cutoff - DAY * (days_ago + 1)


@dataclass
class Pace:
    """How long she actually takes, from recent history."""

    seconds_per_answer: float
    answers_per_new: float  # learning steps taken by a new card on day one
    answers_per_review: float  # 1 + relearning steps after lapses

    def estimate(self, new: int, learn: int, review: int) -> float:
        """Seconds to clear the given queue counts."""
        answers = (
            new * self.answers_per_new
            + learn
            + review * self.answers_per_review
        )
        return answers * self.seconds_per_answer


def pace(col, days: int = 14) -> Pace:
    return _cached(("pace", days), lambda: _pace(col, days))


def _pace(col, days: int) -> Pace:
    since_ms = _day_start(col, days - 1) * 1000
    row = col.db.first(
        "select count(), avg(min(time, ?)) from revlog "
        f"where id >= ? and {ANSWER} and time > 0",
        MAX_ANSWER_SECONDS * 1000,
        since_ms,
    )
    n, avg_ms = row if row else (0, None)
    spa = (
        avg_ms / 1000
        if n and n >= 20 and avg_ms
        else DEFAULT_SECONDS_PER_ANSWER
    )

    # Answers a new card takes on the day it's introduced: only cards with an
    # answer in the window are considered, so this stays fast on big histories.
    per_new = col.db.scalar(
        f"""
        select avg(n) from (
          select (select count() from revlog r where r.cid = f.cid
                  and r.id < f.first + ? and r.{ANSWER.replace(" and ", " and r.")}) n
          from (
            select cid, min(id) first from revlog
            where cid in (select distinct cid from revlog where id >= ?)
              and {ANSWER}
            group by cid
          ) f
          where f.first >= ?
        )""",
        DAY * 1000 // 2,
        since_ms,
        since_ms,
    )
    fail = col.db.scalar(
        "select avg(ease = 1) from revlog where id >= ? and type = 1",
        since_ms,
    )
    return Pace(
        seconds_per_answer=round(spa, 2),
        answers_per_new=per_new or DEFAULT_ANSWERS_PER_NEW,
        answers_per_review=1 + (fail or 0.0),
    )


def queue_counts(col) -> tuple[int, int, int]:
    """(new, learn, review) for the whole collection today, respecting
    daily limits, as the deck list shows them."""
    new = learn = review = 0
    for node in due_tree(col).children:
        new += node.new_count
        learn += node.learn_count
        review += node.review_count
    return new, learn, review


def forecast(col, days: int = 7) -> list[int]:
    """Review cards due on each of the next `days` days (index 0 = today,
    including overdue)."""
    today = col.sched.today
    out = [0] * days
    for offset, count in col.db.all(
        "select max(d - ?, 0), count() from (select case when odid then odue "
        "else due end d from cards where queue in (2, 3)) where d < ? group by 1",
        today,
        today + days,
    ):
        out[offset] += count
    return out


@dataclass
class Retention:
    overall: float | None
    young: float | None  # interval < 21 days
    mature: float | None
    reviews: int


def retention(col, days: int = 30) -> Retention:
    since_ms = _day_start(col, days - 1) * 1000
    row = col.db.first(
        "select count(), avg(ease > 1), "
        "avg(case when lastIvl < 21 then ease > 1 end), "
        "avg(case when lastIvl >= 21 then ease > 1 end) "
        "from revlog where id >= ? and type = 1",
        since_ms,
    )
    n, overall, young, mature = row
    return Retention(overall, young, mature, n or 0)


def daily_counts(col, days: int) -> list[int]:
    """Answers per day for the last `days` days, oldest first (last = today).
    Within a render, one scan of her whole history serves every caller."""
    if _cache is not None:
        full = _cached(
            "daily_full", lambda: _daily_counts(col, history_days(col))
        )
        if days <= len(full):
            return full[-days:]
    return _daily_counts(col, days)


def history_days(col) -> int:
    first = col.db.scalar("select min(id) from revlog") or 0
    return max(1, (col.sched.day_cutoff - first // 1000) // DAY + 1)


def _daily_counts(col, days: int) -> list[int]:
    cutoff = col.sched.day_cutoff
    since = cutoff - days * DAY
    out = [0] * days
    for idx, count in col.db.all(
        "select (id / 1000 - ?) / ?, count() from revlog "
        f"where id >= ? and id < ? and {ANSWER} group by 1",
        since,
        DAY,
        since * 1000,
        cutoff * 1000,
    ):
        if 0 <= idx < days:
            out[int(idx)] += count
    return out


@dataclass
class Streak:
    current: (
        int  # consecutive days up to today (or yesterday, if not yet today)
    )
    longest: int
    studied_today: bool


def streak(col, days: int | None = None) -> Streak:
    if days is None:  # all of her history, so a long-ago best isn't lost
        days = history_days(col)
    counts = daily_counts(col, days)
    studied_today = counts[-1] > 0
    current = 0
    for c in reversed(counts if studied_today else counts[:-1]):
        if not c:
            break
        current += 1
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    return Streak(current, longest, studied_today)


@dataclass
class Today:
    answers: int
    seconds: float


def today(col) -> Today:
    row = col.db.first(
        f"select count(), sum(min(time, 60000)) from revlog where id >= ? and {ANSWER}",
        _day_start(col) * 1000,
    )
    return Today(row[0] or 0, (row[1] or 0) / 1000)


def anki_today(col):
    """The calendar date Anki considers today (before the "next day starts
    at" hour, that's still yesterday's date)."""
    import datetime as dt

    return dt.date.fromtimestamp(col.sched.day_cutoff - DAY)


def format_minutes(seconds: float) -> str:
    minutes = round(seconds / 60)
    if minutes < 1:
        return "under a minute"
    if minutes < 60:
        return f"{minutes} min"
    h, m = divmod(minutes, 60)
    return f"{h} h {m} min" if m else f"{h} h"


def deck_progress(col) -> dict[int, tuple[int, int]]:
    """Today's progress per deck, including subdecks: {deck id: (cards
    answered today, cards still due today)}."""
    done_by_did: dict[int, int] = {}
    for did, n in col.db.all(
        # Credit the deck the card is in now, matching the remaining counts.
        "select c.did, count(distinct r.cid) from revlog r join cards c on "
        "c.id = r.cid where r.id >= ? and r.type in (0, 1, 2, 3) and r.ease > 0 "
        "group by 1",
        _day_start(col) * 1000,
    ):
        done_by_did[did] = n

    out: dict[int, tuple[int, int]] = {}

    def walk(node) -> int:
        done = done_by_did.get(node.deck_id, 0)
        for child in node.children:
            done += walk(child)
        remaining = node.new_count + node.learn_count + node.review_count
        out[node.deck_id] = (done, remaining)
        return done

    for top in due_tree(col).children:
        walk(top)
    return out


def minutes_by_day(col, days: int) -> list[float]:
    """Minutes studied per day for the last `days` days (last = today)."""
    cutoff = col.sched.day_cutoff
    since = cutoff - days * DAY
    out = [0.0] * days
    for idx, ms in col.db.all(
        "select (id / 1000 - ?) / ?, sum(min(time, ?)) from revlog "
        f"where id >= ? and id < ? and {ANSWER} group by 1",
        since,
        DAY,
        MAX_ANSWER_SECONDS * 1000,
        since * 1000,
        cutoff * 1000,
    ):
        if 0 <= idx < days:
            out[int(idx)] = (ms or 0) / 60000
    return out


@dataclass
class WeakSpot:
    did: int
    name: str  # full deck name, e.g. "MCAT::1 Bio-Biochem::Enzymes"
    retention: float
    reviews: int


def weak_spots(
    col, days: int = 30, min_reviews: int = 15, limit: int = 3
) -> list[WeakSpot]:
    """Decks (by the deck each card lives in) with the lowest recall on
    reviews over the last `days` days."""
    since_ms = _day_start(col, days - 1) * 1000
    rows = col.db.all(
        "select case when c.odid then c.odid else c.did end, count(), "
        "avg(r.ease > 1) from revlog r join cards c on c.id = r.cid "
        "where r.id >= ? and r.type = 1 group by 1 having count() >= ?",
        since_ms,
        min_reviews,
    )
    spots = []
    for did, n, acc in rows:
        deck = col.decks.get(did, default=False)
        if deck:
            spots.append(WeakSpot(did, deck["name"], acc, n))
    spots.sort(key=lambda w: (w.retention, -w.reviews))
    return spots[:limit]


@dataclass
class Backlog:
    overdue: int
    extra_per_day: int
    days_to_clear: int


def backlog(col) -> Backlog:
    """Overdue reviews and a gentle catch-up plan: an extra quarter of her
    usual daily reviews (at least 10) on top of what's due anyway."""
    today = col.sched.today
    overdue = col.db.scalar(
        "select count() from cards where queue in (2, 3) and "
        "(case when odid then odue else due end) < ?",
        today,
    )
    recent = daily_counts(col, 14)
    typical = sum(recent) / max(1, sum(1 for c in recent if c))
    extra = max(10, round(typical * 0.25))
    days = -(-overdue // extra) if overdue else 0
    return Backlog(overdue, extra, days)


@dataclass
class FinishLine:
    did: int
    name: str
    unseen: int
    total: int
    per_day: float  # new cards introduced per day, last 14 days
    days_left: int | None  # None when she isn't adding new cards


def finish_lines(col, window: int = 14) -> list[FinishLine]:
    """For each top-level deck with unseen cards: when, at her recent pace
    of new cards, she will have seen every card."""
    since_ms = _day_start(col, window - 1) * 1000
    out = []
    for node in due_tree(col).children:
        dids = [node.deck_id] + [d for _, d in col.decks.children(node.deck_id)]
        ids = ",".join(str(d) for d in dids)
        unseen = col.db.scalar(
            "select count() from cards where type = 0 and "
            f"(case when odid then odid else did end) in ({ids})"
        )
        if not unseen:
            continue
        total = col.db.scalar(
            "select count() from cards where "
            f"(case when odid then odid else did end) in ({ids})"
        )
        introduced = col.db.scalar(
            "select count() from (select r.cid, min(r.id) first from revlog r "
            "join cards c on c.id = r.cid where "
            f"(case when c.odid then c.odid else c.did end) in ({ids}) "
            "and r.type in (0, 1, 2, 3) and r.ease > 0 "
            "group by r.cid) where first >= ?",
            since_ms,
        )
        per_day = introduced / window
        days = -(-unseen // per_day) if per_day > 0 else None
        out.append(
            FinishLine(node.deck_id, node.name, unseen, total, per_day, days)
        )
    return out


@dataclass
class NewCardCost:
    reviews_first_month: float  # answers a new card needs in its first 30 days
    seconds_each: float

    def minutes_per_day(self, new_cards: int) -> float:
        """Extra daily study time, averaged over the next month."""
        return (
            new_cards * self.reviews_first_month * self.seconds_each / 30 / 60
        )


def new_card_cost(col) -> NewCardCost | None:
    """From cards she introduced 30-120 days ago: how many answers each
    needed in its first month."""
    cutoff = col.sched.day_cutoff
    lo, hi = (cutoff - 120 * DAY) * 1000, (cutoff - 30 * DAY) * 1000
    row = col.db.first(
        "select count(), sum(n) from (select f.cid, ("
        "  select count() from revlog r where r.cid = f.cid "
        "  and r.type in (0, 1, 2, 3) and r.ease > 0 and r.id < f.first + ?) n "
        "from (select cid, min(id) first from revlog "
        "      where type in (0, 1, 2, 3) and ease > 0 group by cid) f "
        "where f.first >= ? and f.first < ?)",
        30 * DAY * 1000,
        lo,
        hi,
    )
    cards, answers = row
    if not cards or cards < 10:
        return None
    return NewCardCost(answers / cards, pace(col).seconds_per_answer)
