"""Home-screen briefing and deck overview markup (pure: collection in, HTML
out; hooked up in __init__)."""

import datetime as dt
import json
import html

from . import stats


def script_json(obj) -> str:
    """JSON that is safe inside a <script> element (no "</script>" breakout)."""
    return (
        json.dumps(obj)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


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
        for n in stats.due_tree(col).children
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
        "search": "<circle cx='11' cy='11' r='6.5'/><path d='M16 16l4.5 4.5'/>",
        "inbox": "<path d='M4 13l2.5-7.5h11L20 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z'/>"
        "<path d='M4 13h4.5l1.5 2.5h4l1.5-2.5H20'/>",
        "flag": "<path d='M5.5 21V4.5'/><path d='M5.5 4.5h11l-2 4 2 4h-11'/>",
        "scale": "<path d='M12 4v16M7 20h10M5 7h14'/>"
        "<path d='M5 7l-2.5 6a2.5 2.5 0 0 0 5 0zM19 7l-2.5 6a2.5 2.5 0 0 0 5 0z'/>",
        "target": "<circle cx='12' cy='12' r='8.5'/><circle cx='12' cy='12' r='4.5'/>"
        "<circle cx='12' cy='12' r='0.8'/>",
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


def _tile(
    kind: str,
    icon: str,
    title: str,
    body: str,
    chip: str = "",
    center=False,
    end_note: str = "",
) -> str:
    """A widget card: title row (+ optional context chip), then a body that
    fills the rest and is vertically centered (and horizontally, if asked)."""
    chip_html = f"<span class='jdp-chip'>{chip}</span>" if chip else ""
    align = " jdp-center" if center else ""
    if end_note:
        # Lists sit at the top; a quiet note fills leftover space (shown by
        # home.js only when there's a lot of it).
        align = " jdp-list"
        body += f"<div class='jdp-list-end'><span>{end_note}</span></div>"
    return (
        f"<section class='jdp-tile jdp-tile-{kind}'>"
        f"<h4>{_icon(icon)}<span>{title}</span>{chip_html}</h4>"
        f"<div class='jdp-tile-body{align}'>{body}</div></section>"
    )


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{round(100 * x)}%"


def _short_deck(name: str) -> str:
    """Last part of a deck name, without a leading ordering number
    ("3 Psych-Soc" -> "Psych-Soc")."""
    import re

    leaf = name.split("::")[-1]
    return html.escape(re.sub(r"^\d+[.)]?\s+", "", leaf) or leaf)


# --- Widgets -------------------------------------------------------------
# Each widget renders the inside of one grid item; `cols` is its width in
# grid slots (one slot = the size of the Streak widget).


def _w_forecast(col, settings, cols=1, rows=1) -> str:
    days = stats.forecast(col, 14 if cols >= 3 else 7)
    peak = max(days) or 1
    today = stats.anki_today(col)
    bars = []
    for i, n in enumerate(days):
        day = today + dt.timedelta(days=i)
        label = (
            "today"
            if i == 0
            else (day.strftime("%a") if len(days) <= 7 else str(day.day))
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
        chip=f"{sum(days)} reviews",
    )


def _w_retention(col, settings, cols=1, rows=1) -> str:
    r = stats.retention(col)
    return _tile(
        "green",
        "heart",
        "Memory",
        f"<div class='jdp-big'>{_pct(r.overall)}</div>"
        "<div class='jdp-sub'>remembered this month</div>"
        f"<div class='jdp-pills'><span>young {_pct(r.young)}</span>"
        f"<span>mature {_pct(r.mature)}</span></div>",
        center=True,
    )


def _w_streak(col, settings, cols=1, rows=1) -> str:
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
        f"<div class='jdp-sub'>{note}</div>",
        chip=f"best {s.longest}",
        center=True,
    )


def _w_heatmap(col, settings, cols=1, rows=1) -> str:
    # Columns are weeks (Mon..Sun), ending with the current week.
    today = stats.anki_today(col)
    weeks = WEEKS if cols >= 3 else 24  # same dot size at both widths
    days = weeks * 7 - (6 - today.weekday())
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
            f"<i class='l{level}{today_cls}' title='{day:%a %b} {day.day}: {c} cards'></i>"
        )
    return _tile(
        "accent",
        "dots",
        "Your study days",
        f"<div class='jdp-heatmap'>{''.join(cells)}</div>",
    )


def _w_weak_spots(col, settings, cols=1, rows=1) -> str:
    spots = stats.weak_spots(col, limit=8 if rows >= 2 else 3)
    if not spots:
        body = "<div class='jdp-sub'>Not enough reviews yet this month.</div>"
    else:
        rows_html = "".join(
            "<div class='jdp-meter'>"
            f"<span class='jdp-meter-name' title='{html.escape(w.name)}'>"
            f"{_short_deck(w.name)}</span>"
            f"<span class='jdp-meter-bar'><i style='width:{round(100 * w.retention)}%'>"
            f"</i></span><b>{_pct(w.retention)}</b></div>"
            for w in spots
        )
        body = f"<div class='jdp-meters'>{rows_html}</div>"
        return _tile(
            "learn",
            "search",
            "Weak spots",
            body,
            chip="last 30 days",
            end_note="No other weak spots",
        )
    return _tile("learn", "search", "Weak spots", body, chip="last 30 days")


def _w_backlog(col, settings, cols=1, rows=1) -> str:
    b = stats.backlog(col)
    if not b.overdue:
        check = (
            "<svg class='jdp-check-big' viewBox='0 0 24 24' fill='none' "
            "stroke='currentColor' stroke-width='2.6' stroke-linecap='round' "
            "stroke-linejoin='round' aria-hidden='true'><path d='M5 12.5l4.5 4.5L19 7.5'/>"
            "</svg>"
        )
        return _tile(
            "green",
            "inbox",
            "Backlog",
            f"{check}<div class='jdp-sub'>All caught up</div>",
            center=True,
        )
    else:
        by = (
            stats.anki_today(col) + dt.timedelta(days=b.days_to_clear)
        ).strftime("%a")
        when = "tomorrow" if b.days_to_clear == 1 else f"by {by}"
        body = (
            f"<div class='jdp-big'>{b.overdue}</div>"
            "<div class='jdp-sub'>overdue</div>"
            f"<div class='jdp-pills'><span>+{b.extra_per_day}/day → clear {when}"
            "</span></div>"
        )
    return _tile("learn", "inbox", "Backlog", body, center=True)


def _w_finish_line(col, settings, cols=1, rows=1) -> str:
    lines = stats.finish_lines(col)
    if not lines:
        return _tile(
            "accent",
            "flag",
            "Finish line",
            "<div class='jdp-sub'>You've seen every card in your decks!</div>",
            center=True,
        )
    items = []
    for f in lines[: 8 if rows >= 2 else 3]:
        seen = f.total - f.unseen
        if f.days_left is None:
            when = "<span class='jdp-muted'>paused</span>"
        else:
            date = stats.anki_today(col) + dt.timedelta(days=f.days_left)
            label = (
                f"{date:%b} {date.day}"
                if f.days_left < 300
                else f"{date:%b %Y}"
            )
            when = f"<b>{label}</b>"
        items.append(
            "<div class='jdp-meter jdp-finish'>"
            f"<span class='jdp-meter-name'>{_short_deck(f.name)}</span>"
            f"<span class='jdp-meter-bar' title='{seen} of {f.total} seen'>"
            f"<i style='width:{round(100 * seen / max(1, f.total))}%'></i></span>"
            f"{when}</div>"
        )
    return _tile(
        "accent",
        "flag",
        "Finish line",
        f"<div class='jdp-meters'>{''.join(items)}</div>",
        chip="at your pace",
        end_note="No other decks with unseen cards",
    )


def _w_new_cost(col, settings, cols=1, rows=1) -> str:
    cost = stats.new_card_cost(col)
    if cost is None:
        body = "<div class='jdp-sub'>Needs a month of history</div>"
    else:
        body = (
            f"<div class='jdp-big'>+{cost.minutes_per_day(20):.0f} "
            "<small>min/day</small></div>"
            "<div class='jdp-sub'>if you add 20 new cards today</div>"
            f"<div class='jdp-pills'><span>{cost.reviews_first_month:.1f} reviews "
            "each</span></div>"
        )
    return _tile("sun", "scale", "New-card cost", body, center=True)


def _w_goal(col, settings, cols=1, rows=1) -> str:
    goal = max(5, int(settings["home"]["goal_minutes"]))
    done = stats.minutes_by_day(col, 1)[-1]
    frac = min(1.0, done / goal)
    r = 30
    c = 2 * 3.14159 * r
    reached = done >= goal
    return _tile(
        "green" if reached else "accent",
        "target",
        "Daily goal",
        "<div class='jdp-goal'>"
        "<svg viewBox='0 0 72 72' width='76' height='76' aria-hidden='true'>"
        f"<circle cx='36' cy='36' r='{r}' class='jdp-goal-bg'/>"
        f"<circle cx='36' cy='36' r='{r}' class='jdp-goal-ring' "
        f"stroke-dasharray='{frac * c:.1f} {c:.1f}' transform='rotate(-90 36 36)'/>"
        "</svg>"
        f"<div class='jdp-goal-n'>{round(done)}</div></div>"
        f"<div class='jdp-sub'>{'goal reached!' if reached else f'of {goal} min today'}"
        "</div>"
        "<div class='jdp-goal-adjust'>"
        f"<button title='Lower goal' onclick=\"pycmd('jdp:goal:{goal - 5}')\">−</button>"
        f"<button title='Raise goal' onclick=\"pycmd('jdp:goal:{goal + 5}')\">+</button>"
        "</div>",
        center=True,
    )


def _w_timeline(col, settings, cols=3, rows=1) -> str:
    """One quiet line: today on the left, a dot per upcoming event with a
    short countdown above it. Details (name, date, deck) appear on hover;
    clicking an event linked to a deck studies that deck."""
    today = stats.anki_today(col)
    upcoming = []
    for i, e in enumerate(settings["home"]["events"]):
        try:
            date = dt.date.fromisoformat(e["date"])
        except (KeyError, TypeError, ValueError):
            continue
        if date < today:
            continue
        deck = None
        if isinstance(e.get("deck"), int):
            d = col.decks.get(e["deck"], default=False)
            deck = (d["id"], d["name"]) if d else None
        upcoming.append(
            (i, (date - today).days, date, str(e.get("title", "")), deck)
        )

    deck_options = "".join(
        f"<option value='{d.id}'>{html.escape(d.name.replace('::', ' › '))}</option>"
        for d in sorted(col.decks.all_names_and_ids(), key=lambda d: d.name)
        if d.id != 1 or col.decks.card_count(1, include_subdecks=False)
    )
    form = (
        "<form class='jdp-tl-form' hidden>"
        "<input type='text' name='title' placeholder='Event, e.g. Biochem midterm' "
        "maxlength='60' required>"
        f"<input type='date' name='date' min='{today.isoformat()}' "
        f"max='{today.year + 10}-12-31' required>"
        "<select name='deck' title='Clicking the event will study this deck'>"
        f"<option value=''>No deck</option>{deck_options}</select>"
        "<button type='submit' class='jdp-tl-save'>Add</button>"
        "<button type='button' class='jdp-tl-cancel'>Cancel</button></form>"
    )
    add_btn = "<button type='button' class='jdp-tl-add'>+ Add event</button>"

    def countdown(days: int) -> str:
        return (
            "today" if days == 0 else "1 day" if days == 1 else f"{days} days"
        )

    if not upcoming:
        return (
            "<section class='jdp-tile jdp-tile-accent jdp-timeline'>"
            f"<h4>{_icon('calendar')}<span>Timeline</span>{add_btn}</h4>{form}"
            "<div class='jdp-tile-body jdp-center'><div class='jdp-sub'>Add exams "
            "and deadlines to count down to them.</div></div></section>"
        )

    _, first_days, _, first_title, _ = upcoming[0]
    chip = (
        f"<span class='jdp-chip'>{html.escape(first_title)} · "
        f"{countdown(first_days)}</span>"
    )
    horizon = max(30, round(max(u[1] for u in upcoming) * 1.08))

    def pos(days: int) -> float:
        return 2 + 96 * days / horizon

    months = []
    month = dt.date(today.year, today.month, 1)
    while True:
        month = (month + dt.timedelta(days=32)).replace(day=1)
        d = (month - today).days
        if d > horizon:
            break
        months.append(
            f"<span class='jdp-tl-month' style='left:{pos(d):.1f}%'>"
            f"{month.strftime('%b')}</span>"
        )

    dots = []
    for i, days, date, title, deck in upcoming:
        soon = " jdp-soon" if days <= 7 else ""
        deck_html, click = "", ""
        if deck:
            deck_html = f"<span class='jdp-tl-pop-deck'>Study {_short_deck(deck[1])} →</span>"
            click = f" onclick=\"pycmd('jdp:study:{deck[0]}')\""
        short = "today" if days == 0 else f"{days} d"
        dots.append(
            f"<div class='jdp-tl-event{soon}{' jdp-tl-linked' if deck else ''}' "
            f"style='left:{pos(days):.1f}%' tabindex='0'{click}>"
            f"<span class='jdp-tl-count'>{short}</span><i class='jdp-tl-dot'></i>"
            "<div class='jdp-tl-pop' role='tooltip'>"
            f"<b>{html.escape(title)}</b>"
            f"<span>{date:%a, %b} {date.day} · {countdown(days)}</span>"
            f"{deck_html}"
            f"<button type='button' class='jdp-tl-del' title='Remove event' "
            f"data-title='{html.escape(title)}' data-date='{date.isoformat()}' "
            'onclick="event.stopPropagation();this.disabled=true;'
            "pycmd('jdp:event-del:'+JSON.stringify("
            '{title:this.dataset.title,date:this.dataset.date}))">'
            "Remove</button></div></div>"
        )
    return (
        "<section class='jdp-tile jdp-tile-accent jdp-timeline'>"
        f"<h4>{_icon('calendar')}<span>Timeline</span>{chip}{add_btn}</h4>{form}"
        "<div class='jdp-tile-body'><div class='jdp-tl'>"
        "<div class='jdp-tl-line'></div>"
        "<span class='jdp-tl-today'>today</span>"
        f"{''.join(months)}{''.join(dots)}</div></div></section>"
    )


WIDGETS = {
    # id: (name, description, allowed sizes as (cols, rows), first = default,
    #      render(col, settings, cols, rows))
    "timeline": (
        "Timeline",
        "Days until your exams and milestones",
        [(3, 1)],
        _w_timeline,
    ),
    "forecast": (
        "Coming up",
        "Reviews due over the next one or two weeks",
        [(2, 1), (3, 1)],
        _w_forecast,
    ),
    "streak": ("Streak", "Days in a row you've studied", [(1, 1)], _w_streak),
    "goal": (
        "Daily goal",
        "Today's study time against your goal",
        [(1, 1)],
        _w_goal,
    ),
    "retention": (
        "Memory",
        "How much you remembered this month",
        [(1, 1)],
        _w_retention,
    ),
    "backlog": (
        "Backlog",
        "Overdue cards and a plan to catch up",
        [(1, 1)],
        _w_backlog,
    ),
    "new_cost": (
        "New-card cost",
        "What new cards add to future reviews",
        [(1, 1)],
        _w_new_cost,
    ),
    "weak_spots": (
        "Weak spots",
        "The topics you're forgetting most",
        [(2, 1), (2, 2)],
        _w_weak_spots,
    ),
    "finish_line": (
        "Finish line",
        "When you'll have seen every card",
        [(2, 1), (2, 2)],
        _w_finish_line,
    ),
    "heatmap": (
        "Your study days",
        "Your study activity, day by day",
        [(3, 1), (2, 1)],
        _w_heatmap,
    ),
}


# What each size means, shown while resizing in edit mode.
SIZE_LABELS = {
    "forecast": {(2, 1): "7 days", (3, 1): "14 days"},
    "heatmap": {(2, 1): "6 months", (3, 1): "8 months"},
    "weak_spots": {(2, 1): "Top 3", (2, 2): "Top 8"},
    "finish_line": {(2, 1): "3 decks", (2, 2): "8 decks"},
}


def parse_entry(entry: str) -> tuple[str, tuple[int, int]] | None:
    """'forecast' or 'forecast:3x1' -> (id, size); None if unknown/invalid.
    Sizes not allowed for the widget fall back to its default."""
    wid, _, size = str(entry).partition(":")
    if wid not in WIDGETS:
        return None
    sizes = WIDGETS[wid][2]
    try:
        c, r = (int(x) for x in size.split("x"))
        if (c, r) in sizes:
            return wid, (c, r)
    except ValueError:
        pass
    return wid, sizes[0]


def _widget(wid: str, size: tuple[int, int], col, settings) -> str:
    name, desc, sizes, render = WIDGETS[wid]
    cols, rows = size
    try:
        inner = render(col, settings, cols, rows)
    except Exception:  # one broken widget must never break the home screen
        inner = _tile(
            "accent",
            "dots",
            html.escape(name),
            "<div class='jdp-sub'>Couldn't load this widget.</div>",
        )
    allowed = ",".join(f"{c}x{r}" for c, r in sizes)
    labels = ";".join(
        f"{c}x{r}={label}" for (c, r), label in SIZE_LABELS.get(wid, {}).items()
    )
    return (
        f"<div class='jdp-widget jdp-cols-{cols} jdp-rows-{rows}' data-id='{wid}' "
        f"data-name='{html.escape(name)}' data-desc='{html.escape(desc)}' "
        f"data-size='{cols}x{rows}' data-sizes='{allowed}' "
        f"data-labels='{html.escape(labels)}' data-cols='{cols}'>"
        f"{inner}</div>"
    )


def home_html(col, settings: dict, now: dt.datetime | None = None) -> str:
    with stats.render_cache():
        return _home_html(col, settings, now)


def _catalog_shell(wid: str) -> str:
    """A catalog entry for the "Add widget" picker: metadata only. Its real
    content is rendered when she adds it (the page re-renders)."""
    name, desc, sizes, _render = WIDGETS[wid]
    cols, rows = sizes[0]
    allowed = ",".join(f"{c}x{r}" for c, r in sizes)
    return (
        f"<div class='jdp-widget jdp-cols-{cols} jdp-rows-{rows}' data-id='{wid}' "
        f"data-name='{html.escape(name)}' data-desc='{html.escape(desc)}' "
        f"data-size='{cols}x{rows}' data-sizes='{allowed}' data-cols='{cols}' "
        "data-shell='1'></div>"
    )


def _home_html(col, settings: dict, now: dt.datetime | None = None) -> str:
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
    layout, seen = [], set()
    for entry in settings["home"]["widgets"]:
        parsed = parse_entry(entry)
        if parsed and parsed[0] not in seen:
            seen.add(parsed[0])
            layout.append(parsed)
    grid = "".join(_widget(w, size, col, settings) for w, size in layout)
    # Every widget not on the grid, pre-rendered for the "Add widget" picker.
    catalog = "".join(_catalog_shell(w) for w in WIDGETS if w not in seen)
    return (
        f"<header class='jdp-hello'>{head}</header>"
        "<div class='jdp-insights'>"
        f"<div class='jdp-grid'>{grid}</div>"
        f"<template id='jdp-catalog'>{catalog}</template>"
        "<div class='jdp-edit-bar'><button class='jdp-link jdp-edit-toggle' "
        "type='button'>Edit widgets</button></div></div>"
    )


_ACTION_ICONS = {
    "plus": "<path d='M12 5v14M5 12h14'/>",
    "import": "<path d='M12 4v10M8 10l4 4 4-4'/>"
    "<path d='M4 15v2a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-2'/>",
    "globe": "<circle cx='12' cy='12' r='8.5'/>"
    "<path d='M3.5 12h17M12 3.5c2.4 2.4 3.6 5.2 3.6 8.5S14.4 18.1 12 20.5"
    "C9.6 18.1 8.4 15.3 8.4 12S9.6 5.9 12 3.5z'/>",
}


def _link(cmd: str, label: str, key: str = "", icon: str = "") -> str:
    title = f" title='Shortcut: {key}'" if key else ""
    svg = (
        "<svg class='jdp-ico' viewBox='0 0 24 24' fill='none' "
        "stroke='currentColor' stroke-width='2' stroke-linecap='round' "
        f"stroke-linejoin='round' aria-hidden='true'>{_ACTION_ICONS[icon]}</svg>"
        if icon
        else ""
    )
    return (
        f"<button class='jdp-link'{title} "
        f"onclick=\"pycmd('{cmd}');return false;\">{svg}{label}</button>"
    )


def deck_progress_script(col) -> str:
    """Today's progress per started deck, for web/deckbrowser.js to draw as
    a thin line under each deck name."""
    data = {
        str(did): [done, rem]
        for did, (done, rem) in stats.deck_progress(col).items()
        if done
    }
    return f"<script>window.JDP_DECK_PROGRESS = {script_json(data)};</script>"


def deck_actions() -> str:
    """The deck screen's own actions (formerly a separate bottom bar)."""
    return (
        "<div class='jdp-deck-actions'>"
        + _link("create", "New deck", icon="plus")
        + _link("import", "Import a file", icon="import")
        + _link("shared", "Find shared decks", icon="globe")
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
