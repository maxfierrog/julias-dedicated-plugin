"""Julia's Dedicated Plugin: a personal, maintained Anki study suite.

Anki imports this package at startup from ``addons21/<folder>``, where the
folder is the manifest's package name for file installs but a numeric ID for
AnkiWeb installs (so never hardcode it). Module-level code runs inside the GUI
process: keep it to hook registration and do real work in the hooks.
"""

from aqt import gui_hooks, mw
from aqt.toolbar import HideMode

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
    if s["modules"]["briefing"]:
        content.stats = briefing.home_html(mw.col, s) + content.stats


@_guard
def _on_overview(overview, content) -> None:
    if web.settings()["modules"]["theme"]:
        content.table = briefing.overview_table(mw.col, stats.pace(mw.col))


def study_deck(did: int) -> None:
    """Start reviewing a deck directly, skipping its overview screen."""
    mw.col.decks.select(did)
    mw.col.startTimebox()
    mw.moveToState("review")


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
    if new_state != "review":
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
    on = web.settings()["session"]["focus_mode"]
    mw.pm.set_hide_top_bar(on)
    if on:
        mw.pm.set_top_bar_hide_mode(HideMode.ALWAYS)


# --- Messages from our web UI -------------------------------------------


def _on_js_message(handled, message: str, context):
    if not message.startswith("jdp:"):
        return handled
    cmd, _, arg = message[4:].partition(":")
    try:
        if cmd == "study":
            study_deck(int(arg))
        elif cmd == "settings":
            from .settings_dialog import open_settings

            open_settings()
        elif cmd in ("set", "reset", "feedback"):
            from .settings_dialog import handle

            handle(cmd, arg)
        elif cmd == "decks":
            mw.moveToState("deckBrowser")
        elif cmd == "fatigue-dismiss" and _session is not None:
            _session.fatigue_dismissed = True
            _push_session()
    except Exception:
        log.exception("error handling %s", message)
    return (True, None)


# --- Toolbar ------------------------------------------------------------------


def _on_toolbar_links(links: list[str], toolbar) -> None:
    def open_settings():
        from .settings_dialog import open_settings as show

        show()

    links.append(
        toolbar.create_link(
            "jdp-settings",
            "Customize",
            open_settings,
            tip="Julia's Dedicated Plugin settings",
            id="jdp-settings",
        )
    )


# --- Startup ----------------------------------------------------------------


@_guard
def _on_collection_loaded(col) -> None:
    apply_focus_mode()
    # The toolbar was first drawn before her settings were readable.
    mw.toolbar.draw()


def _on_main_window_init() -> None:
    from .settings_dialog import add_menu_action

    add_menu_action()
    log.info("Julia's Dedicated Plugin %s loaded", __version__)


mw.addonManager.setWebExports(__name__, web.WEB_EXPORTS)
gui_hooks.webview_will_set_content.append(
    _guard(web.on_webview_will_set_content)
)
gui_hooks.webview_did_receive_js_message.append(_on_js_message)
gui_hooks.deck_browser_will_render_content.append(_on_deck_browser)
gui_hooks.overview_will_render_content.append(_on_overview)
gui_hooks.state_did_change.append(_on_state_change)
gui_hooks.reviewer_did_answer_card.append(_on_answer)
gui_hooks.reviewer_did_show_question.append(_on_show_question)
gui_hooks.top_toolbar_did_init_links.append(_on_toolbar_links)
gui_hooks.collection_did_load.append(_on_collection_loaded)
gui_hooks.main_window_did_init.append(_on_main_window_init)
