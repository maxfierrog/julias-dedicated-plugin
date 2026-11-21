"""Study statistics computed from the collection (no GUI imports, so this is
unit-tested against a seeded collection).

Day boundaries follow Anki's: a day starts at the "next day starts at" hour
(`col.sched.day_cutoff` is the end of today).
"""

from dataclasses import dataclass

DAY = 86_400
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
    since_ms = _day_start(col, days - 1) * 1000
    row = col.db.first(
        "select count(), avg(min(time, ?)) from revlog "
        "where id >= ? and type in (0, 1, 2, 3) and time > 0",
        MAX_ANSWER_SECONDS * 1000,
        since_ms,
    )
    n, avg_ms = row if row else (0, None)
    spa = (
        avg_ms / 1000
        if n and n >= 20 and avg_ms
        else DEFAULT_SECONDS_PER_ANSWER
    )

    # Answers a new card takes on the day it's introduced.
    per_new = col.db.scalar(
        """
        select avg(n) from (
          select count() n from revlog r
          where r.id >= ? and r.id < (
            select min(id) from revlog r2 where r2.cid = r.cid
          ) + ? and r.cid in (
            select cid from revlog group by cid having min(id) >= ?
          )
          group by r.cid
        )""",
        since_ms,
        DAY * 1000 // 2,
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
    for node in col.sched.deck_due_tree().children:
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
        "select max(due - ?, 0), count() from cards "
        "where queue in (2, 3) and due < ? group by 1",
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
    """Answers per day for the last `days` days, oldest first (last = today)."""
    cutoff = col.sched.day_cutoff
    since = cutoff - days * DAY
    out = [0] * days
    for idx, count in col.db.all(
        "select (id / 1000 - ?) / ?, count() from revlog "
        "where id >= ? and id < ? group by 1",
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


def streak(col, days: int = 365) -> Streak:
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
        "select count(), sum(time) from revlog where id >= ?",
        _day_start(col) * 1000,
    )
    return Today(row[0] or 0, (row[1] or 0) / 1000)


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
        "select case when c.odid then c.odid else c.did end, count(distinct r.cid) "
        "from revlog r join cards c on c.id = r.cid where r.id >= ? group by 1",
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

    for top in col.sched.deck_due_tree().children:
        walk(top)
    return out
