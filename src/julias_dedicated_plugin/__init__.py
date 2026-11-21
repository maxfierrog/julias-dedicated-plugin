"""Julia's Dedicated Plugin: a personal, maintained Anki study suite.

Anki imports this package at startup from ``addons21/<folder>``, where the
folder is the manifest's package name for file installs but a numeric ID for
AnkiWeb installs (so never hardcode it). Module-level code runs inside the GUI
process: keep it to hook registration and do real work in the hooks.
"""

import datetime as dt
import json
import os
import sys

from aqt import gui_hooks, mw
from aqt.qt import QEvent, QMenu, QObject, Qt, QTimer, QWidget

from . import briefing, session, stats, web
from .version import __version__

log = mw.addonManager.get_logger(__name__)

_session: session.Session | None = None
_pace: stats.Pace | None = None


def _guard(fn):
    """Never let one of our features break Anki's screens: log and move on."""

    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            log.exception("error in %s", fn.__name__)

    wrapper.__name__ = fn.__name__
    return wrapper


# --- Home and overview ------------------------------------------------------


@_guard
def _on_deck_browser(deck_browser, content) -> None:
    s = web.settings()
    extra = (
        briefing.deck_actions() + briefing.deck_progress_script(mw.col)
        if s["modules"]["theme"]
        else ""
    )
    if s["modules"]["briefing"]:
        extra += briefing.home_html(mw.col, s)
    content.stats = extra + content.stats


@_guard
def _on_overview(overview, content) -> None:
    if web.settings()["modules"]["theme"]:
        content.table = briefing.overview_table(mw.col, stats.pace(mw.col))


def study_deck(did: int) -> None:
    """Start reviewing a deck directly, skipping its overview screen. With
    nothing due, show the overview instead (Anki's congratulations screen,
    with custom study), rather than an empty review."""
    mw.col.decks.select(did)
    if sum(mw.col.sched.counts()):
        mw.col.startTimebox()
        mw.moveToState("review")
    else:
        mw.moveToState("overview")


@_guard
def _on_deck_options_menu(menu, did: int) -> None:
    """The deck's gear menu gains the actions that used to live only on its
    overview screen (which clicking a deck now skips)."""
    if not web.settings()["modules"]["theme"]:
        return

    def custom_study():
        import aqt.customstudy

        mw.col.decks.select(did)
        aqt.customstudy.CustomStudy.fetch_data_and_show(mw)

    def description():
        from aqt.deckdescription import DeckDescriptionDialog

        mw.col.decks.select(did)
        DeckDescriptionDialog(mw)

    menu.addSeparator()
    menu.addAction("Custom study…").triggered.connect(custom_study)
    if not mw.col.decks.get(did)["dyn"]:
        menu.addAction("Description…").triggered.connect(description)


# --- Session display ------------------------------------------------------


def _current_session() -> session.Session:
    # Created on first use: Anki shows the first card before it announces
    # the state change to "review".
    global _session, _pace
    if _session is None:
        _session = session.Session()
        _pace = stats.pace(mw.col)
    return _session


def _push_session() -> None:
    if mw.state != "review":
        return
    _current_session()
    s = web.settings()
    if not s["modules"]["session"]:
        return
    payload = session.state(_session, mw.col.sched.counts(), _pace, s)
    mw.reviewer.web.eval(session.js_update(payload))


@_guard
def _on_state_change(new_state, old_state) -> None:
    global _session
    if new_state == "review":
        _hide_top_bar_for_review()
    else:
        _session = None


@_guard
def _on_answer(reviewer, card, ease) -> None:
    _current_session().record(ease, card.time_taken() / 1000)


@_guard
def _on_show_question(card) -> None:
    _push_session()


# --- Focus mode -------------------------------------------------------------


@_guard
def apply_focus_mode() -> None:
    """Focus mode keeps the top bar hidden for the whole review session.

    We deliberately don't use Anki's own auto-hide: it re-shows the bar
    whenever the mouse leaves the card (e.g. moving to the answer buttons),
    which feels random. Anki's preference is switched off and we hide the
    bar ourselves on entering review; Anki shows it again on leaving."""
    if web.settings()["session"]["focus_mode"]:
        mw.pm.set_hide_top_bar(False)
    if mw.state == "review":
        _hide_top_bar_for_review()


def _hide_top_bar_for_review() -> None:
    if mw.state != "review":
        return
    if web.settings()["session"]["focus_mode"]:
        mw.toolbarWeb.hide()
    else:
        mw.toolbarWeb.show()


def _strict_json(text: str):
    def reject(name):
        raise ValueError(f"invalid JSON constant {name}")

    return json.loads(text, parse_constant=reject)


def _home_command(cmd: str, arg: str) -> None:
    """Edits made directly on home-screen widgets."""
    from .settings import MAX_EVENT_TITLE, MAX_EVENT_YEARS, Settings

    store = Settings(mw.col)
    today = dt.date.today()
    # Past events are no longer shown or removable: drop them on any edit.
    events = [
        e
        for e in store.get()["home"]["events"]
        if e["date"] >= today.isoformat()
    ]
    if cmd == "goal":
        store.set("home.goal_minutes", int(arg))
    elif cmd == "event-add":
        data = _strict_json(arg)
        title = str(data.get("title", "")).strip()[:MAX_EVENT_TITLE]
        date = dt.date.fromisoformat(str(data.get("date", "")))
        if (
            not title
            or date < today
            or date.year > today.year + MAX_EVENT_YEARS
        ):
            return
        deck = data.get("deck")
        deck = int(deck) if str(deck or "").isdigit() else None
        if deck is not None and not mw.col.decks.get(deck, default=False):
            deck = None
        event = {"title": title, "date": date.isoformat()}
        if deck is not None:
            event["deck"] = deck
        if not any(
            e["title"] == title and e["date"] == event["date"] for e in events
        ):  # a double submit adds it once
            events.append(event)
            events.sort(key=lambda e: e["date"])
        store.set("home.events", events)
    elif cmd == "event-del":
        # By identity, not position: a double click can't remove a neighbour.
        data = _strict_json(arg)
        for i, e in enumerate(events):
            if e["title"] == data.get("title") and e["date"] == data.get(
                "date"
            ):
                del events[i]
                break
        store.set("home.events", events)
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()


# --- Messages from our web UI -------------------------------------------
# Any page can call pycmd(), including card templates from shared decks, so
# every command is only accepted from the screen that legitimately sends it.

_FROM_HOME = {
    "study",
    "settings",
    "home-refresh",
    "goal",
    "event-add",
    "event-del",
}
_FROM_SETTINGS = {"set", "reset", "feedback"}
_FROM_REVIEWER = {"decks", "fatigue-dismiss"}  # harmless navigation only
_DEV = {"dev-grab", "dev-tooltip", "dev-zoom", "dev-close-popup"}


def _allowed(cmd: str, arg: str, context) -> bool:
    import aqt.deckbrowser
    import aqt.reviewer
    import aqt.toolbar

    from .settings_dialog import SettingsContext

    home = isinstance(context, aqt.deckbrowser.DeckBrowser)
    if cmd in _FROM_SETTINGS and isinstance(context, SettingsContext):
        return True
    if cmd == "set" and home:
        # Edit mode saves only the widget layout from the home screen.
        try:
            return _strict_json(arg)[0] == "home.widgets"
        except (ValueError, TypeError, IndexError, KeyError):
            return False
    if cmd in _FROM_HOME:
        return home
    if cmd in _FROM_REVIEWER:
        return isinstance(context, aqt.reviewer.Reviewer)
    if cmd in _DEV:
        return bool(os.environ.get("ANKIDEV")) and isinstance(
            context, aqt.toolbar.TopToolbar
        )
    return False


def _on_js_message(handled, message: str, context):
    if not message.startswith("jdp:"):
        return handled
    cmd, _, arg = message[4:].partition(":")
    if not _allowed(cmd, arg, context):
        log.warning("ignored %r from %s", cmd, type(context).__name__)
        return (True, None)
    try:
        if cmd == "study":
            study_deck(int(arg))
        elif cmd == "settings":
            from .settings_dialog import open_settings

            open_settings()
        elif cmd == "home-refresh":
            if mw.state == "deckBrowser":
                mw.deckBrowser.refresh()
        elif cmd in ("goal", "event-add", "event-del"):
            _home_command(cmd, arg)
        elif cmd in ("set", "reset", "feedback"):
            from .settings_dialog import handle

            handle(cmd, arg)
        elif cmd == "dev-grab":
            _dev_grab(arg)
        elif cmd == "dev-tooltip":
            from aqt.qt import QCursor, QToolTip

            QToolTip.showText(QCursor.pos(), arg or "Back to decks (D)")
        elif cmd == "dev-zoom":
            from . import zoom

            zoom.apply(float(arg))
        elif cmd == "dev-close-popup":
            from aqt.qt import QApplication

            if popup := QApplication.activePopupWidget():
                popup.close()
        elif cmd == "decks":
            mw.moveToState("deckBrowser")
        elif cmd == "fatigue-dismiss" and _session is not None:
            _session.fatigue_dismissed = True
            _push_session()
    except Exception:
        log.exception("error handling %s", cmd)
    return (True, None)


def _dev_grab(folder: str) -> None:
    """Dev only: save a PNG of every visible top-level window (native Qt
    windows can't be captured over DevTools)."""
    from aqt.qt import QApplication

    for i, w in enumerate(QApplication.topLevelWidgets()):
        if w.isVisible() and w.isWindow():
            name = f"{i:02d}-{type(w).__name__}.png"
            w.grab().save(os.path.join(folder, name))


# --- Window title bars ------------------------------------------------------


class _WindowWatcher(QObject):
    """Styles each top-level window's title bar as it is first shown, and
    lets popups (menus, tooltips) have truly rounded corners."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Polish and _is_rounded_popup(obj):
            # Without a transparent window behind it, a rounded menu shows
            # the native window's square corners. Must be set before showing.
            obj.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            obj.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            obj.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        if (
            event.type() == QEvent.Type.Show
            and isinstance(obj, QWidget)
            and obj.isWindow()
            and obj.windowType() in (Qt.WindowType.Window, Qt.WindowType.Dialog)
        ):
            # After the native window exists and Qt has set its look.
            QTimer.singleShot(0, lambda w=obj: web.style_window(w))
        return False


def _is_rounded_popup(obj) -> bool:
    # Tooltips are Qt's private QTipLabel (seen from Python as a QLabel), so
    # check the C++ class name rather than the Python type. macOS only (on
    # Linux without a compositor, translucent windows render black), and
    # only with the theme on.
    if sys.platform != "darwin":
        return False
    if not (
        isinstance(obj, QMenu)
        or (isinstance(obj, QObject) and obj.inherits("QTipLabel"))
    ):
        return False
    return web.settings()["modules"]["theme"]


_watcher = _WindowWatcher()


# --- Startup ----------------------------------------------------------------


@_guard
def _on_collection_loaded(col) -> None:
    from . import zoom

    zoom.apply()
    apply_focus_mode()
    from . import qt_theme

    qt_theme.apply(web.settings())
    web.apply_window_chrome()
    # The toolbar was first drawn before her settings were readable.
    mw.toolbar.draw()


@_guard
def _on_main_window_init() -> None:
    from . import zoom
    from .settings_dialog import add_menu_action

    add_menu_action()
    zoom.install()
    # Tools > Add-ons > Config opens our Customize window (settings live in
    # the collection, not in Anki's per-add-on JSON config).
    from .settings_dialog import open_settings

    mw.addonManager.setConfigAction(__name__, open_settings)
    mw.app.installEventFilter(_watcher)
    log.info("Julia's Dedicated Plugin %s loaded", __version__)


mw.addonManager.setWebExports(__name__, web.WEB_EXPORTS)
gui_hooks.webview_will_set_content.append(
    _guard(web.on_webview_will_set_content)
)
gui_hooks.webview_did_receive_js_message.append(_on_js_message)


def _on_style_init(buf: str) -> str:
    from . import qt_theme

    try:
        return qt_theme.on_style_did_init(buf)
    except Exception:
        log.exception("qt style")
        return buf


gui_hooks.style_did_init.append(_on_style_init)
gui_hooks.webview_did_inject_style_into_page.append(
    _guard(web.on_webview_did_inject_style)
)
gui_hooks.deck_browser_will_render_content.append(_on_deck_browser)
gui_hooks.overview_will_render_content.append(_on_overview)
gui_hooks.deck_browser_will_show_options_menu.append(_on_deck_options_menu)
gui_hooks.state_did_change.append(_on_state_change)
gui_hooks.reviewer_did_answer_card.append(_on_answer)
gui_hooks.reviewer_did_show_question.append(_on_show_question)
gui_hooks.collection_did_load.append(_on_collection_loaded)


def _on_profile_will_close() -> None:
    from .settings_dialog import close_settings

    close_settings()


def _on_sync_finished() -> None:
    from . import qt_theme, zoom
    from .settings_dialog import reload_settings

    # Settings may have changed on another computer: re-apply everything
    # that isn't read live (native windows, title bars, focus mode, zoom).
    reload_settings()
    qt_theme.apply(web.settings())
    apply_focus_mode()
    zoom.apply()
    web.refresh_live()


gui_hooks.profile_will_close.append(_guard(_on_profile_will_close))
gui_hooks.sync_did_finish.append(_guard(_on_sync_finished))
# Anki updates its Qt palette on theme change; restyle after it does.
gui_hooks.theme_did_change.append(
    lambda: QTimer.singleShot(0, _guard(web.apply_window_chrome))
)
gui_hooks.main_window_did_init.append(_on_main_window_init)
