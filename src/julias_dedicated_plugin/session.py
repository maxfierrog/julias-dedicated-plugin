"""Session display: progress, time left and (optionally) a fatigue signal.

Python tracks the session and pushes a small JSON state into the reviewer
web view; web/session.js renders it.
"""

import json
import time
from dataclasses import dataclass, field

from . import stats

FATIGUE_MIN_MINUTES = 25
FATIGUE_MIN_ANSWERS = 40
FATIGUE_WINDOW = 15


@dataclass
class Session:
    started: float = field(default_factory=time.time)
    answers: list[tuple[int, float]] = field(default_factory=list)  # ease, s
    fatigue_dismissed: bool = False

    def record(self, ease: int, seconds: float) -> None:
        self.answers.append((ease, min(seconds, stats.MAX_ANSWER_SECONDS)))


def fatigue(session: Session, now: float | None = None) -> bool:
    """True when the end of a long session is clearly worse than its start:
    noticeably less accurate, or slower and somewhat less accurate."""
    now = now or time.time()
    a = session.answers
    if (
        session.fatigue_dismissed
        or (now - session.started) / 60 < FATIGUE_MIN_MINUTES
        or len(a) < FATIGUE_MIN_ANSWERS
    ):
        return False

    def window(xs):
        acc = sum(e > 1 for e, _ in xs) / len(xs)
        secs = sum(s for _, s in xs) / len(xs)
        return acc, secs

    acc0, s0 = window(a[: max(FATIGUE_WINDOW, len(a) // 3)])
    acc1, s1 = window(a[-FATIGUE_WINDOW:])
    drop = acc0 - acc1
    slower = s1 > s0 * 1.35
    return drop >= 0.15 or (slower and drop >= 0.07)


def state(
    session: Session,
    counts: tuple[int, int, int],
    pace: stats.Pace,
    settings: dict,
    now: float | None = None,
) -> dict:
    now = now or time.time()
    new, learn, review = counts
    remaining = new + learn + review
    eta = pace.estimate(new, learn, review)
    done = len(session.answers)
    finish = time.localtime(now + eta)
    return {
        "show_progress": settings["session"]["show_progress"],
        "show_eta": settings["session"]["show_eta"],
        "done": done,
        "remaining": remaining,
        "progress": done / (done + remaining) if done + remaining else 1.0,
        "eta": stats.format_minutes(eta) if remaining else "",
        "finish": _clock(finish) if remaining else "",
        "minutes": round((now - session.started) / 60),
        "fatigue": settings["modules"]["fatigue"] and fatigue(session, now),
    }


def _clock(t: time.struct_time) -> str:
    """'4:37 PM' without platform-specific strftime flags (Windows lacks them)."""
    hour = t.tm_hour % 12 or 12
    return f"{hour}:{t.tm_min:02d} {'AM' if t.tm_hour < 12 else 'PM'}"


def js_update(payload: dict) -> str:
    return f"window.jdpSession && jdpSession.update({json.dumps(payload)});"
