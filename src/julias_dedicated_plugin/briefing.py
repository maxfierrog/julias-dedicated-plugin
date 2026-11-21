"""Home-screen briefing and deck overview markup (pure: collection in, HTML
out; hooked up in __init__)."""

import datetime as dt
import json
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


def _icon(name: str) -> str:
    """Small hand-drawn style icons (stroke = currentColor)."""
    paths = {
        "calendar": "<rect x='4' y='5.5' width='16' height='14' rx='4'/>"
        "<path d='M8 3.5v4M16 3.5v4M4 10.5h16'/>",
        "heart": "<path d='M12 19.5s-7-4.3-7-9.4A3.9 3.9 0 0 1 12 8a3.9 3.9 0 0 1 "
        "7 2.1c0 5.1-7 9.4-7 9.4z'/>",
        "flame": "<path d='M12 20.5c3.3 0 6-2.4 6-5.8 0-3.9-3.4-5.6-3.9-9.7-2.6 "
        "1.6-4 4.1-4 6.3-1.2-.6-1.8-1.9-1.9-3.1C6.9 9.8 6 11.9 6 14.7c0 3.4 2.7 "
        "5.8 6 5.8z'/>",
        "dots": "<circle cx='7' cy='8' r='1.6'/><circle cx='12' cy='8' r='1.6'/>"
        "<circle cx='17' cy='8' r='1.6'/><circle cx='7' cy='13' r='1.6'/>"
        "<circle cx='12' cy='13' r='1.6'/><circle cx='7' cy='18' r='1.6'/>",
    }
    return (
        "<svg class='jdp-ico' viewBox='0 0 24 24' fill='none' "
        "stroke='currentColor' stroke-width='2' stroke-linecap='round' "
        f"stroke-linejoin='round' aria-hidden='true'>{paths[name]}</svg>"
    )


SPARKLE = (
    "<svg class='jdp-sparkle' viewBox='0 0 24 24' aria-hidden='true'>"
    "<path d='M12 2c.6 4.6 2.4 6.9 7 7.9-4.6 1-6.4 3.3-7 8.1-.6-4.8-2.4-7.1-7-8.1 "
    "4.6-1 6.4-3.3 7-7.9z'/></svg>"
)
BLOB = (
    "<svg class='jdp-blob' viewBox='0 0 600 260' preserveAspectRatio='none' "
    "aria-hidden='true'><path d='M38 132C22 66 92 18 190 26c84 7 120-22 214-12 "
    "98 11 176 52 168 126-8 70-92 104-196 106-98 2-128-22-214-14C78 238 52 192 "
    "38 132z'/></svg>"
)


def _study_button(col, pace: stats.Pace) -> str:
    target = primary_deck(col)
    if target is None:
        return ""
    did, name, due = target
    return (
        f"<button class='jdp-primary jdp-cta' "
        f"onclick=\"pycmd('jdp:study:{did}');return false;\">"
        f"<span>Study {html.escape(name)}</span>"
        f"<small>{due}</small></button>"
    )


def _summary_line(col, pace: stats.Pace) -> str:
    new, learn, review = stats.queue_counts(col)
    total = new + learn + review
    done = stats.today(col)
    if total == 0:
        if done.answers:
            return (
                f"All done for today: <b>{done.answers} cards</b> in "
                f"<b>{stats.format_minutes(done.seconds)}</b>. Nice work!"
            )
        return "Nothing due today. Enjoy the break!"
    eta = stats.format_minutes(pace.estimate(new, learn, review))
    cards = "card" if total == 1 else "cards"
    return f"You have <b>{total} {cards}</b> today, about <b>{eta}</b>."


def _tile(kind: str, icon: str, title: str, body: str) -> str:
    return (
        f"<section class='jdp-tile jdp-tile-{kind}'>"
        f"<h4>{_icon(icon)}{title}</h4>{body}</section>"
    )


def _forecast_tile(col) -> str:
    days = stats.forecast(col, 7)
    peak = max(days) or 1
    today = dt.date.today()
    bars = []
    for i, n in enumerate(days):
        label = (
            "today" if i == 0 else (today + dt.timedelta(days=i)).strftime("%a")
        )
        h = max(8, round(60 * n / peak)) if n else 6
        bars.append(
            f"<div class='jdp-bar{' jdp-today' if i == 0 else ''}' "
            f"title='{n} due'><span class='jdp-bar-n'>{n}</span>"
            f"<i style='height:{h}px'></i><span>{label}</span></div>"
        )
    return _tile(
        "accent",
        "calendar",
        "Coming up",
        f"<div class='jdp-bars'>{''.join(bars)}</div>",
    )


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{round(100 * x)}%"


def _retention_tile(col) -> str:
    r = stats.retention(col)
    return _tile(
        "green",
        "heart",
        "Memory",
        f"<div class='jdp-big'>{_pct(r.overall)}</div>"
        "<div class='jdp-sub'>of reviews remembered this month"
        f"<br><span class='jdp-muted'>young {_pct(r.young)} · mature "
        f"{_pct(r.mature)}</span></div>",
    )


def _streak_tile(col) -> str:
    s = stats.streak(col)
    if s.current:
        note = "Done for today!" if s.studied_today else "Keep it going today"
    else:
        note = "A fresh start today"
    unit = "day" if s.current == 1 else "days"
    return _tile(
        "sun",
        "flame",
        "Streak",
        f"<div class='jdp-big'>{s.current} <small>{unit}</small></div>"
        f"<div class='jdp-sub'>{note}<br><span class='jdp-muted'>best: "
        f"{s.longest} days</span></div>",
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
        today_cls = " jdp-now" if i == len(counts) - 1 else ""
        cells.append(
            f"<i class='l{level}{today_cls}' title='{day:%a %b %-d}: {c} cards'></i>"
        )
    return (
        "<section class='jdp-tile jdp-heat'>"
        f"<h4>{_icon('dots')}Your study days</h4>"
        f"<div class='jdp-heatmap'>{''.join(cells)}</div></section>"
    )


def home_html(col, settings: dict, now: dt.datetime | None = None) -> str:
    b = settings["briefing"]
    now = now or dt.datetime.now()
    pace = stats.pace(col)
    title = greeting(settings["name"], now.hour) if b["greeting"] else "Today"
    head = (
        f"<div class='jdp-hello-text'>{BLOB}"
        f"<h1>{title}{SPARKLE}</h1>"
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


def _link(cmd: str, label: str, key: str = "") -> str:
    title = f" title='Shortcut: {key}'" if key else ""
    return (
        f"<button class='jdp-link'{title} "
        f"onclick=\"pycmd('{cmd}');return false;\">{label}</button>"
    )


def deck_progress_script(col) -> str:
    """Today's progress per started deck, for web/deckbrowser.js to draw as
    a thin line under each deck name."""
    data = {
        str(did): [done, rem]
        for did, (done, rem) in stats.deck_progress(col).items()
        if done
    }
    return f"<script>window.JDP_DECK_PROGRESS = {json.dumps(data)};</script>"


def deck_actions() -> str:
    """The deck screen's own actions (formerly a separate bottom bar)."""
    return (
        "<div class='jdp-deck-actions'>"
        + _link("create", "+ New deck")
        + _link("import", "Import a file")
        + _link("shared", "Find shared decks")
        + "</div>"
    )


def overview_actions(col) -> str:
    """A deck's own actions (formerly a separate bottom bar)."""
    links = [_link("opts", "Options", "O")]
    dyn = col.decks.current()["dyn"]
    if dyn:
        links += [
            _link("refresh", "Rebuild", "R"),
            _link("empty", "Empty", "E"),
        ]
    else:
        links.append(_link("studymore", "Custom study", "C"))
    if col.sched.have_buried():
        links.append(_link("unbury", "Unbury", "U"))
    if not dyn:
        links.append(_link("description", "Description"))
    return f"<div class='jdp-secondary'>{''.join(links)}</div>"


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
    return (
        f"<div class='jdp-counts'>{tiles}</div><div class='jdp-go'>{action}</div>"
        + overview_actions(col)
    )
