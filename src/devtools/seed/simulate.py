"""Simulate months of realistic review history on a fresh collection.

Anki numbers days from the collection creation time (`crt`). We move `crt`
back `days` days, replay a student's study habits day by day with a simplified
SM-2 scheduler (Anki's default), and write the resulting revlog rows and
final card states directly. "Today" (day `days`) is left unstudied, so the
collection opens with a realistic due queue.

Modeled on purpose, so features have something to detect:
- per-card difficulty (notes marked hard become likely leeches),
- skipped days, a multi-day exam break, and a backlog going into today,
- unfinished sessions when the daily time budget runs out,
- fatigue: accuracy drops and answer times rise late in long sessions.
"""

import heapq
import math
import random
import time
from dataclasses import dataclass

from anki.collection import Collection

DAY = 86_400
LEARN_STEPS = (60, 600)  # seconds; Anki's default 1m 10m
RELEARN_STEP = 600
GRADUATING_IVL, EASY_IVL = 1, 4
MAX_ANSWER_MS = 60_000

# card.type / card.queue / revlog.type values used by Anki
CARD_REVIEW, QUEUE_REVIEW, QUEUE_SUSPENDED = 2, 2, -1
REV_LEARN, REV_REVIEW, REV_RELEARN = 0, 1, 2
AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4


@dataclass
class SimCard:
    cid: int
    nid: int
    difficulty: float  # 0 = trivial .. 1 = brutal
    ivl: int = 0
    factor: int = 2500
    due: int = 0
    last_day: int = 0
    reps: int = 0
    lapses: int = 0
    introduced: bool = False
    suspended: bool = False


class Simulator:
    def __init__(self, col: Collection, days: int, seed: int, hard_nids):
        self.col = col
        self.days = days
        self.rng = random.Random(seed)
        self.revlog: list[tuple] = []
        self.leech_nids: set[int] = set()
        self._last_ms = 0
        self._last_answer_s = 0.0
        conf = col.decks.config_dict_for_deck_id(1)
        self.leech_fails = conf["lapse"]["leechFails"]
        self.leech_suspends = conf["lapse"]["leechAction"] == 0
        self.rev_limit = conf["rev"]["perDay"]
        self.max_ivl = conf["rev"]["maxIvl"]

        rows = col.db.all(
            "select id, nid from cards where type = 0 order by due, ord"
        )
        self.new_queue: list[SimCard] = []
        for cid, nid in rows:
            if nid in hard_nids:
                d = self.rng.uniform(0.75, 1.0)
            else:
                d = self.rng.betavariate(2, 6)
            self.new_queue.append(SimCard(cid, nid, d))
        self.cards = list(self.new_queue)

    # --- memory model ---------------------------------------------------

    def _recall_p(self, c: SimCard, day: int, position: int) -> float:
        elapsed = max(1, day - c.last_day)
        # Easy cards outlast their interval; hard ones decay much faster.
        stability = max(0.5, c.ivl * (1.6 - 1.5 * c.difficulty))
        p = 0.9 ** (elapsed / stability)
        fatigue = max(0.85, 1 - 0.0004 * position)
        return p * fatigue

    def _answer_ms(self, ease: int, c: SimCard, position: int) -> int:
        median = {AGAIN: 12_000, HARD: 10_000, GOOD: 6_500, EASY: 3_500}[ease]
        median *= 1 + 0.6 * c.difficulty
        median *= 1 + position / 400  # slowing down as the session drags on
        ms = self.rng.lognormvariate(math.log(median), 0.45)
        return int(min(MAX_ANSWER_MS, max(1_200, ms)))

    def _success_grade(self, c: SimCard) -> int:
        r = self.rng.random()
        if r < 0.05 + 0.25 * c.difficulty:
            return HARD
        if r > 1 - 0.15 * (1 - c.difficulty):
            return EASY
        return GOOD

    def _fuzz(self, ivl: int) -> int:
        if ivl < 3:
            return ivl
        return max(1, round(ivl * self.rng.uniform(0.95, 1.05)))

    # --- revlog ---------------------------------------------------------

    def _log(self, t: float, c: SimCard, ease, ivl, last_ivl, factor, ms, kind):
        rid = max(int(t * 1000), self._last_ms + 1)
        self._last_ms = rid
        self.revlog.append(
            (rid, c.cid, -1, ease, ivl, last_ivl, factor, ms, kind)
        )
        c.reps += 1

    # --- one study day --------------------------------------------------

    def _study_day(self, day: int, day_start: int, n_new: int) -> None:
        rng = self.rng
        due = [
            c
            for c in self.cards
            if c.introduced and not c.suspended and c.due <= day
        ]
        due.sort(key=lambda c: (c.due, rng.random()))
        due = due[: self.rev_limit]
        new = [
            self.new_queue.pop(0)
            for _ in range(min(n_new, len(self.new_queue)))
        ]

        # Interleave new cards evenly among reviews, as Anki's v3 default does.
        main: list[tuple[str, SimCard]] = [("rev", c) for c in due]
        for i, c in enumerate(new):
            pos = round((i + 1) * len(main) / (len(new) + 1)) if main else i
            main.insert(pos, ("new", c))

        # Evening session (6pm-10:30pm local), sometimes a morning one too.
        t = day_start + rng.uniform(14, 18.5) * 3600
        budget = rng.uniform(35, 110) * 60
        if rng.random() < 0.25:
            t = day_start + rng.uniform(5, 7) * 3600
        session_start = t

        learning: list[tuple[float, int, int, SimCard]] = []  # heap
        position = 0
        seq = 0

        while main or learning:
            over_budget = t - session_start > budget
            if learning and (learning[0][0] <= t or not main or over_budget):
                ready, _, step, c = heapq.heappop(learning)
                t = max(t, ready)
                step = self._learning_answer(t, c, step, position, day)
                if step is not None:
                    delay = RELEARN_STEP if step < 0 else LEARN_STEPS[step]
                    seq += 1
                    heapq.heappush(learning, (t + delay, seq, step, c))
            elif main and not over_budget:
                kind, c = main.pop(0)
                if kind == "new":
                    c.introduced = True
                    step = self._learning_answer(t, c, 0, position, day)
                else:
                    step = self._review_answer(t, c, position, day)
                if step is not None:
                    delay = RELEARN_STEP if step < 0 else LEARN_STEPS[step]
                    seq += 1
                    heapq.heappush(learning, (t + delay, seq, step, c))
            else:
                # Out of time: unanswered reviews stay due (backlog); unseen
                # new cards go back to the front of the new queue.
                self.new_queue[:0] = [c for k, c in main if k == "new"]
                break
            position += 1
            t += self._last_answer_s + rng.uniform(1, 4)
            if rng.random() < 0.01:
                t += rng.uniform(120, 900)  # phone, snack, etc.

    def _learning_answer(self, t, c: SimCard, step: int, position, day):
        """Answer a (re)learning card. Returns the next step or None when it
        graduates. step < 0 means relearning after a lapse."""
        relearning = step < 0
        p_ok = 0.92 - 0.45 * c.difficulty
        p_ok *= max(0.85, 1 - 0.0004 * position)
        if self.rng.random() >= p_ok:
            ease = AGAIN
        elif (
            not relearning
            and step == 0
            and self.rng.random() < 0.08 * (1 - c.difficulty)
        ):
            ease = EASY
        else:
            ease = GOOD
        ms = self._answer_ms(ease, c, position)
        self._last_answer_s = ms / 1000
        kind = REV_RELEARN if relearning else REV_LEARN
        cur = -(RELEARN_STEP if relearning else LEARN_STEPS[step])

        if ease == AGAIN:
            nxt = -1 if relearning else 0
            nxt_ivl = -(RELEARN_STEP if relearning else LEARN_STEPS[0])
            self._log(
                t,
                c,
                ease,
                nxt_ivl,
                cur,
                0 if not relearning else c.factor,
                ms,
                kind,
            )
            return nxt
        if ease == EASY:
            c.ivl = EASY_IVL
        elif relearning:
            c.ivl = max(1, c.ivl)
        elif step + 1 < len(LEARN_STEPS):
            self._log(t, c, ease, -LEARN_STEPS[step + 1], cur, 0, ms, kind)
            return step + 1
        else:
            c.ivl = GRADUATING_IVL
        self._log(
            t, c, ease, c.ivl, cur, c.factor if relearning else 0, ms, kind
        )
        c.last_day, c.due = day, day + c.ivl
        return None

    def _review_answer(self, t, c: SimCard, position: int, day: int):
        p = self._recall_p(c, day, position)
        ease = self._success_grade(c) if self.rng.random() < p else AGAIN
        ms = self._answer_ms(ease, c, position)
        self._last_answer_s = ms / 1000
        last = c.ivl
        overdue = max(0, day - c.due)

        if ease == AGAIN:
            c.lapses += 1
            c.factor = max(1300, c.factor - 200)
            c.ivl = 1
            self._log(t, c, ease, -RELEARN_STEP, last, c.factor, ms, REV_REVIEW)
            if c.lapses >= self.leech_fails and (
                (c.lapses - self.leech_fails) % max(1, self.leech_fails // 2)
                == 0
            ):
                self.leech_nids.add(c.nid)
                if self.leech_suspends:
                    c.suspended = True
            return -1

        if ease == HARD:
            ivl = max(last + 1, round(last * 1.2))
            c.factor = max(1300, c.factor - 150)
        else:
            ivl = max(last + 1, round((last + overdue / 2) * c.factor / 1000))
            if ease == EASY:
                ivl = max(ivl + 1, round(ivl * 1.3))
                c.factor += 150
        c.ivl = min(self.max_ivl, self._fuzz(ivl))
        self._log(t, c, ease, c.ivl, last, c.factor, ms, REV_REVIEW)
        c.last_day, c.due = day, day + c.ivl
        return None

    # --- driver ---------------------------------------------------------

    def run(self) -> None:
        rng, days = self.rng, self.days
        crt = self.col.crt - days * DAY
        self.col.crt = crt

        brk = int(days * rng.uniform(0.5, 0.65))
        exam_break = set(range(brk, brk + rng.randint(4, 6)))
        skip_tail = {days - 1, days - 2}
        # Spread new cards so most are introduced by the end, as a student
        # pacing a deck to an exam date would (Anki's cap is 20/day default,
        # but students commonly raise it).
        study_days = days * 0.92 * 0.85 - len(exam_break) - len(skip_tail)
        mean_new = max(2.0, 0.8 * len(self.new_queue) / max(1, study_days))
        for day in range(days):
            if day in exam_break or day in skip_tail or rng.random() < 0.08:
                continue
            n_new = (
                max(0, round(rng.gauss(mean_new, mean_new / 3)))
                if rng.random() < 0.85
                else 0
            )
            self._study_day(day, crt + day * DAY, n_new)
        self._write()

    def _write(self) -> None:
        db = self.col.db
        db.executemany(
            "insert into revlog (id, cid, usn, ease, ivl, lastIvl, factor, "
            "time, type) values (?,?,?,?,?,?,?,?,?)",
            self.revlog,
        )
        now = int(time.time())
        for c in self.cards:
            if not c.introduced:
                continue
            db.execute(
                "update cards set type=?, queue=?, due=?, ivl=?, factor=?, "
                "reps=?, lapses=?, left=0, mod=?, usn=-1 where id=?",
                CARD_REVIEW,
                QUEUE_SUSPENDED if c.suspended else QUEUE_REVIEW,
                c.due,
                c.ivl,
                c.factor,
                c.reps,
                c.lapses,
                now,
                c.cid,
            )
        for nid in self.leech_nids:
            note = self.col.get_note(nid)
            note.add_tag("leech")
            self.col.update_note(note, skip_undo_entry=True)


def simulate(col: Collection, days: int = 120, seed: int = 0, hard_nids=()):
    """Write `days` of simulated history. Requires a collection with no
    review history yet (e.g. freshly seeded or freshly imported)."""
    if col.db.scalar("select count() from revlog"):
        raise ValueError("collection already has review history")
    sim = Simulator(col, days, seed, set(hard_nids))
    sim.run()
    # Let Anki derive per-card fields newer versions cache (e.g. last review
    # time) from the revlog we just wrote.
    col.fix_integrity()
    return sim
