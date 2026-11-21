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


def on_webview_will_set_content(web_content: WebContent, context) -> None:
    ctx = context_name(context)
    if ctx is None:
        return
    s = settings()
    web_content.css.append(url("fonts.css"))
    if s["modules"]["theme"]:
        web_content.css.append(url("theme.css"))
    web_content.head += _apply_script(s, ctx)
    if ctx == "deckbrowser":
        web_content.js.append(url("deckbrowser.js"))
    if ctx == "reviewer":
        # Always loaded; html classes switch them on/off, so toggling a
        # module in settings applies live without reloading the reviewer.
        web_content.css += [url("cards.css"), url("session.css")]
        web_content.js += [url("cards.js"), url("session.js")]
        web_content.body += (
            "<button id='jdp-exit' title='Back to decks (D)' "
            "onclick=\"pycmd('jdp:decks');return false;\">← Decks</button>"
        )


def apply_js(s: dict | None = None) -> str:
    s = s or settings()
    args = f"{json.dumps(theme.tokens_css(s))}, {json.dumps(theme.html_classes(s))}"
    return f"window.jdpApply && jdpApply({args});"


def refresh_live() -> None:
    """Push current settings into every open main-window web view without
    reloading them (keeps the current card, scroll position, etc.)."""
    js = apply_js()
    for web in (mw.web, mw.toolbar.web, mw.bottomWeb):
        web.eval(js)


def rerender() -> None:
    """Re-render the current screen, for changes that alter markup."""
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    elif mw.state == "overview":
        mw.overview.refresh()
    mw.toolbar.redraw()
    refresh_live()
