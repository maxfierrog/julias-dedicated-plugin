"""Home-screen briefing and deck overview markup (pure: collection in, HTML
out; hooked up in __init__)."""

import datetime as dt
import html

from . import stats

WEEKS = 36
GEAR = (
    "<svg viewBox='0 0 24 24' width='18' height='18' fill='none' "
    "stroke='currentColor' stroke-width='1.8' stroke-linecap='round' "
    "stroke-linejoin='round'><circle cx='12' cy='12' r='3'/><path d='M19.4 "
    "15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 "
    "0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 "
    "0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 "
    "0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 "
    "1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 "
    "1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 "
    "0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 "
    "0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z'/></svg>"
)


def greeting(name: str, hour: int) -> str:
    part = (
        "Good morning"
        if 4 <= hour < 12
        else "Good afternoon" if 12 <= hour < 18 else "Good evening"
    )
    return f"{part}, {html.escape(name)}" if name.strip() else part


def primary_deck(col) -> tuple[int, str, int] | None:
    """The top-level deck the big Study button should start: the one she's
    currently in if it has work, else the one with the most due.
    Returns (deck id, name, cards due) or None if nothing is due."""
    nodes = [
        (n.deck_id, n.name, n.new_count + n.learn_count + n.review_count)
        for n in col.sched.deck_due_tree().children
    ]
    nodes = [n for n in nodes if n[2] > 0]
    if not nodes:
        return None
    current = col.decks.get_current_id()
    for did, name, due in nodes:
        if did == current or current in {
            cid for _, cid in col.decks.children(did)
        }:
            return did, name, due
    return max(nodes, key=lambda n: n[2])


def _study_button(col, pace: stats.Pace) -> str:
    target = primary_deck(col)
    if target is None:
        return ""
    did, name, due = target
    return (
        f"<button class='jdp-primary jdp-cta' "
        f"onclick=\"pycmd('jdp:study:{did}');return false;\">"
        f"<span>Study {html.escape(name)}</span>"
        f"<small>{due} cards</small></button>"
    )


def _summary_line(col, pace: stats.Pace) -> str:
    new, learn, review = stats.queue_counts(col)
    total = new + learn + review
    done = stats.today(col)
    if total == 0:
        if done.answers:
            return (
                f"All done for today: <b>{done.answers}</b> answers in "
                f"<b>{stats.format_minutes(done.seconds)}</b>."
            )
        return "Nothing due today."
    eta = stats.format_minutes(pace.estimate(new, learn, review))
    parts = [f"<b>{review + learn}</b> to review"]
    if new:
        parts.append(f"<b>{new}</b> new")
    line = " · ".join(parts) + f" · about <b>{eta}</b>"
    if done.answers:
        line += f" <span class='jdp-muted'>({done.answers} done)</span>"
    return line


def _forecast_tile(col) -> str:
    days = stats.forecast(col, 7)
    peak = max(days) or 1
    today = dt.date.today()
    bars = []
    for i, n in enumerate(days):
        label = (
            "Today" if i == 0 else (today + dt.timedelta(days=i)).strftime("%a")
        )
        h = max(4, round(64 * n / peak)) if n else 2
        bars.append(
            f"<div class='jdp-bar' title='{n} due'>"
            f"<span class='jdp-bar-n'>{n}</span>"
            f"<i style='height:{h}px'></i><span>{label}</span></div>"
        )
    return (
        "<section class='jdp-tile'><h4>Next 7 days</h4>"
        f"<div class='jdp-bars'>{''.join(bars)}</div></section>"
    )


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{round(100 * x)}%"


def _retention_tile(col) -> str:
    r = stats.retention(col)
    return (
        "<section class='jdp-tile'><h4>Retention · 30 days</h4>"
        f"<div class='jdp-big'>{_pct(r.overall)}</div>"
        f"<div class='jdp-sub'>Young {_pct(r.young)} · Mature {_pct(r.mature)}"
        f"<br>{r.reviews} reviews</div></section>"
    )


def _streak_tile(col) -> str:
    s = stats.streak(col)
    if s.current:
        note = (
            "Keep it going today" if not s.studied_today else "Done for today"
        )
    else:
        note = "A fresh start today"
    unit = "day" if s.current == 1 else "days"
    return (
        "<section class='jdp-tile'><h4>Streak</h4>"
        f"<div class='jdp-big'>{s.current} <small>{unit}</small></div>"
        f"<div class='jdp-sub'>{note}<br>Longest: {s.longest} days</div>"
        "</section>"
    )


def _heatmap(col) -> str:
    # Columns are weeks (Mon..Sun), ending with the current week.
    today = dt.date.today()
    days = WEEKS * 7 - (6 - today.weekday())
    counts = stats.daily_counts(col, days)
    nonzero = sorted(c for c in counts if c)
    # Levels relative to her own typical day, so the map stays meaningful.
    q = nonzero[len(nonzero) // 2] if nonzero else 1
    cells = []
    start = today - dt.timedelta(days=days - 1)
    for i, c in enumerate(counts):
        day = start + dt.timedelta(days=i)
        level = (
            0
            if not c
            else 1 if c < q * 0.5 else 2 if c < q else 3 if c < q * 1.6 else 4
        )
        cells.append(
            f"<i class='l{level}' title='{day:%a %b %-d}: {c} answers'></i>"
        )
    return (
        "<section class='jdp-tile jdp-heat'><h4>Last "
        f"{WEEKS} weeks</h4><div class='jdp-heatmap'>{''.join(cells)}</div>"
        "</section>"
    )


def home_html(col, settings: dict, now: dt.datetime | None = None) -> str:
    b = settings["briefing"]
    now = now or dt.datetime.now()
    pace = stats.pace(col)
    title = greeting(settings["name"], now.hour) if b["greeting"] else "Today"
    head = (
        "<div class='jdp-hello-text'>"
        f"<h1>{title}</h1>"
        f"<p class='jdp-summary'>{_summary_line(col, pace)}</p></div>"
        "<div class='jdp-hello-actions'>"
        f"{_study_button(col, pace)}"
        "<button class='jdp-icon' title='Customize' aria-label='Customize' "
        "onclick=\"pycmd('jdp:settings');return false;\">"
        f"{GEAR}</button></div>"
    )
    tiles = []
    if b["forecast"]:
        tiles.append(_forecast_tile(col))
    if b["retention"]:
        tiles.append(_retention_tile(col))
    tiles.append(_streak_tile(col))
    body = f"<div class='jdp-tiles'>{''.join(tiles)}</div>"
    if b["heatmap"]:
        body += _heatmap(col)
    return (
        f"<header class='jdp-hello'>{head}</header>"
        f"<div class='jdp-insights'>{body}</div>"
    )


def overview_table(col, pace: stats.Pace) -> str:
    """Replaces the overview's count table: stat tiles + time estimate."""
    new, learn, review = col.sched.counts()
    total = new + learn + review
    eta = (
        stats.format_minutes(pace.estimate(new, learn, review)) if total else ""
    )

    def tile(kind, label, n):
        return f"<div class='jdp-count jdp-{kind}'><b>{n}</b><span>{label}</span></div>"

    tiles = (
        tile("new", "New", new)
        + tile("learn", "Learning", learn)
        + tile("review", "Review", review)
    )
    if total:
        action = (
            "<button id='study' class='jdp-primary' autofocus "
            "onclick=\"pycmd('study');return false;\">Study now</button>"
            f"<div class='jdp-eta'>about {eta}</div>"
        )
    else:
        action = "<div class='jdp-eta'>Nothing due in this deck today.</div>"
    return f"<div class='jdp-counts'>{tiles}</div><div class='jdp-go'>{action}</div>"
