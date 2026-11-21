"""The Customize window: one place for every option, applied live to the
main window behind it."""

import json

from aqt import mw
from aqt.qt import QAction, QDialog, QKeySequence, QVBoxLayout
from aqt.theme import Theme
from aqt.webview import AnkiWebView

from . import theme, web
from .settings import Settings
from .version import __version__

FEEDBACK_URL = (
    "https://github.com/maxfierrog/julias-dedicated-plugin/issues/new"
)

# Settings whose change alters page markup, not just tokens/classes.
_RERENDER_PREFIXES = ("modules.", "briefing.", "name", "theme.ui_font")

_dialog: "SettingsDialog | None" = None


class _Context:
    jdp_context = "settings"


def _page_data() -> dict:
    presets = {
        key: {
            "name": p.name,
            "light": [p.light.canvas, p.light.elevated, p.light.accent],
            "dark": [p.dark.canvas, p.dark.elevated, p.dark.accent],
        }
        for key, p in theme.PRESETS.items()
    }
    return {
        "settings": web.settings(),
        "presets": presets,
        "mode": int(mw.pm.theme()),
        "version": __version__,
    }


class SettingsDialog(QDialog):
    jdp_themed = True  # web content in our theme: title bar uses our canvas

    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle("Customize")
        self.resize(480, 780)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.web = AnkiWebView(parent=self, title="jdp settings")
        layout.addWidget(self.web)
        self.web.stdHtml(
            "<div id='app'></div><script>window.JDP_DATA = "
            f"{json.dumps(_page_data())};</script>",
            css=[web.url("settings.css")],
            js=[web.url("settings.js")],
            context=_Context(),
        )
        # Sit beside the main window so changes are visible as they happen.
        geo = mw.frameGeometry()
        self.move(max(0, geo.right() - self.width() - 24), geo.top() + 64)

    def closeEvent(self, event) -> None:
        global _dialog
        _dialog = None
        self.web.cleanup()
        super().closeEvent(event)

    def push(self) -> None:
        self.web.eval(
            f"window.jdpSettings && jdpSettings.load({json.dumps(_page_data())});"
        )


def open_settings() -> None:
    global _dialog
    if mw.col is None:
        return
    if _dialog is None:
        _dialog = SettingsDialog()
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()


def handle(cmd: str, arg: str) -> None:
    """Commands from the settings page (routed by the add-on's message hook)."""
    from . import apply_focus_mode

    if cmd == "set":
        path, value = json.loads(arg)
        if path == "anki.mode":
            mw.set_theme(Theme(int(value)))
        else:
            Settings(mw.col).set(path, value)
        if path == "session.focus_mode":
            apply_focus_mode()
        if path.startswith(_RERENDER_PREFIXES):
            web.rerender()
        else:
            web.refresh_live()
    elif cmd == "reset":
        Settings(mw.col).reset()
        apply_focus_mode()
        web.rerender()
        if _dialog:
            _dialog.push()
    elif cmd == "feedback":
        from urllib.parse import quote

        from anki.buildinfo import version as anki_version
        from aqt.utils import openLink

        body = (
            "**What happened / what would you like?**\n\n\n\n---\n"
            f"Plugin {__version__} · Anki {anki_version}"
        )
        openLink(f"{FEEDBACK_URL}?body={quote(body)}")
    if _dialog:
        _dialog.web.eval(web.apply_js())
        refresh = json.dumps(web.settings())
        _dialog.web.eval(f"window.jdpSettings && jdpSettings.sync({refresh});")


def add_menu_action() -> None:
    action = QAction("Customize Julia's Dedicated Plugin…", mw)
    action.setShortcut(QKeySequence("Ctrl+Shift+,"))
    action.triggered.connect(open_settings)
    mw.form.menuTools.addAction(action)
