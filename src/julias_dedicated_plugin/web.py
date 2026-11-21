"""Injecting our CSS/JS into Anki's web screens, and updating them live.

Each Anki screen is a web view whose content is assembled in Python; the
`webview_will_set_content` hook lets us add stylesheets, scripts and markup.
Screens are identified by the `context` object Anki passes along.
"""

import json

import aqt.deckbrowser
import aqt.overview
import aqt.reviewer
import aqt.toolbar
from aqt import mw
from aqt.webview import WebContent

from . import theme
from .settings import Settings, merged

WEB_EXPORTS = r"web/.*\.(css|js|woff2|svg|html|png)$"


def folder() -> str:
    # Never hardcode: AnkiWeb installs us under a numeric folder name.
    return mw.addonManager.addon_from_module(__name__)


def url(path: str) -> str:
    return f"/_addons/{folder()}/web/{path}"


def settings() -> dict:
    # Before a profile is open (e.g. the toolbar's first draw) use defaults.
    return Settings(mw.col).get() if mw.col else merged(None)


def context_name(context) -> str | None:
    """Which of our styled screens a web view context belongs to."""
    checks = (
        (aqt.deckbrowser.DeckBrowser, "deckbrowser"),
        (aqt.deckbrowser.DeckBrowserBottomBar, "bottombar"),
        (aqt.overview.Overview, "overview"),
        (aqt.overview.OverviewBottomBar, "bottombar"),
        (aqt.reviewer.Reviewer, "reviewer"),
        (aqt.reviewer.ReviewerBottomBar, "reviewer-bottom"),
        (aqt.toolbar.TopToolbar, "toolbar"),
        (aqt.toolbar.BottomToolbar, "bottombar"),
    )
    for cls, name in checks:
        if isinstance(context, cls):
            return name
    return getattr(context, "jdp_context", None)


def _apply_script(s: dict, ctx: str) -> str:
    """Defines window.jdpApply (used for live updates) and applies now."""
    tokens = theme.tokens_css(s)
    classes = theme.html_classes(s)
    return f"""<script>
window.jdpApply = function (css, classes) {{
  let tag = document.getElementById("jdp-tokens");
  if (!tag) {{
    tag = document.createElement("style");
    tag.id = "jdp-tokens";
    document.head.appendChild(tag);
  }}
  tag.textContent = css;
  const root = document.documentElement;
  [...root.classList].filter(c => c.startsWith("jdp")).forEach(
    c => root.classList.remove(c));
  root.classList.add(...classes, "jdp-ctx-{ctx}");
  document.dispatchEvent(new CustomEvent("jdp:settings"));
}};
jdpApply({json.dumps(tokens)}, {json.dumps(classes)});
</script>"""


def _tokens_only_js(s: dict) -> str:
    """For Anki's functional screens (editor, deck options, stats, card
    info...): only our palette tokens, which Anki's own CSS already uses. No
    layout or font changes; those screens keep their shape."""
    css = json.dumps(theme.tokens_css(s) + theme.bootstrap_css(s))
    return (
        "(function(){let t=document.getElementById('jdp-tokens');"
        "if(!t){t=document.createElement('style');t.id='jdp-tokens';"
        f"document.head.appendChild(t);}}t.textContent={css};}})();"
    )


def on_webview_did_inject_style(webview) -> None:
    """Newer page-based screens (deck options, stats, editor...)."""
    s = settings()
    if s["modules"]["theme"] and mw.col is not None:
        webview.eval(_tokens_only_js(s))


def on_webview_will_set_content(web_content: WebContent, context) -> None:
    ctx = context_name(context)
    if ctx is None:
        # A functional screen we don't redesign: palette tokens only.
        s = settings()
        if s["modules"]["theme"] and mw.col is not None:
            web_content.head += (
                f"<style id='jdp-tokens'>{theme.tokens_css(s)}"
                f"{theme.bootstrap_css(s)}</style>"
            )
        return
    s = settings()
    web_content.css.append(url("fonts.css"))
    if s["modules"]["theme"]:
        web_content.css.append(url("theme.css"))
    web_content.head += _apply_script(s, ctx)
    if ctx == "reviewer":
        # Always loaded; html classes switch them on/off, so toggling a
        # module in settings applies live without reloading the reviewer.
        web_content.css += [url("cards.css"), url("session.css")]
        web_content.js += [url("cards.js"), url("session.js")]


def apply_js(s: dict | None = None) -> str:
    s = s or settings()
    args = f"{json.dumps(theme.tokens_css(s))}, {json.dumps(theme.html_classes(s))}"
    return f"window.jdpApply && jdpApply({args});"


def apply_window_chrome() -> None:
    """Blend every open window's title bar into its own background (macOS),
    or restore the stock title bars when the theme is off."""
    from aqt.qt import QApplication

    for widget in QApplication.topLevelWidgets():
        # The main window may not be shown yet when her collection loads.
        if widget.isVisible() or widget is mw:
            style_window(widget)


def style_window(widget) -> None:
    from aqt.qt import QPalette
    from aqt.theme import theme_manager

    from . import mac_window

    if not widget.isWindow() or mw.col is None and widget is not mw:
        return
    try:
        s = settings()
        if not s["modules"]["theme"]:
            mac_window.restore_title_bar(widget)
            return
        if widget is mw or getattr(widget, "jdp_themed", False):
            # Web-based windows we theme: match our canvas.
            color = theme.canvas_color(s, theme_manager.night_mode)
        else:
            # Native Qt windows (Browse, Add, dialogs): match their own fill.
            color = widget.palette().color(QPalette.ColorRole.Window).name()
        mac_window.blend_title_bar(widget, color)
    except Exception:
        mw.addonManager.get_logger(__name__).exception("title bar")


def refresh_live() -> None:
    """Push current settings into every open main-window web view without
    reloading them (keeps the current card, scroll position, etc.)."""
    from . import qt_theme

    from aqt.qt import QApplication
    from aqt.webview import AnkiWebView

    s = settings()
    main = apply_js(s)
    tokens = (
        _tokens_only_js(s)
        if s["modules"]["theme"]
        else ("document.getElementById('jdp-tokens')?.remove();")
    )
    # Every open web view: redesigned screens re-apply fully, functional
    # screens (editor, options, stats...) just get the palette.
    for w in QApplication.allWidgets():
        if isinstance(w, AnkiWebView):
            w.eval(f"if (window.jdpApply) {{ {main} }} else {{ {tokens} }}")
    try:
        qt_theme.apply(settings())  # re-styles native windows, then title bars
    except Exception:
        mw.addonManager.get_logger(__name__).exception("qt theme")
    apply_window_chrome()


def rerender() -> None:
    """Re-render the current screen, for changes that alter markup."""
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    elif mw.state == "overview":
        mw.overview.refresh()
    mw.toolbar.draw()
    refresh_live()
