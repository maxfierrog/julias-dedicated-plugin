"""The Customize window: one place for every option, applied live to the
main window behind it."""

import json

from aqt import mw
from aqt.qt import QAction, QDialog, QKeySequence, Qt, QVBoxLayout
from aqt.theme import Theme
from aqt.webview import AnkiWebView

from . import theme, web
from .briefing import script_json
from .settings import Settings
from .version import __version__

FEEDBACK_URL = (
    "https://github.com/maxfierrog/julias-dedicated-plugin/issues/new"
)

# Settings whose change alters page markup, not just tokens/classes.
_RERENDER_PREFIXES = ("modules.", "briefing.", "name")

_dialog: "SettingsDialog | None" = None


class SettingsContext:
    """Bridge context of the Customize window: commands that change settings
    are only accepted from here (see __init__._allowed)."""

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
        # Really free the window (and its web view) when closed.
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Customize")
        self.resize(480, 780)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.web = AnkiWebView(parent=self, title="jdp settings")
        self._ctx = SettingsContext()
        # Messages from this page carry our context (checked on receipt).
        self.web.set_bridge_command(lambda _cmd: None, self._ctx)
        layout.addWidget(self.web)
        self.web.stdHtml(
            "<div id='app'></div><script>window.JDP_DATA = "
            f"{script_json(_page_data())};</script>",
            css=[web.url("settings.css")],
            js=[web.url("settings.js")],
            context=self._ctx,
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


def close_settings() -> None:
    """Profile closing: never let the window write into another profile."""
    if _dialog is not None:
        _dialog.close()


def reload_settings() -> None:
    """After a sync, show the (possibly changed) synced settings."""
    if _dialog is not None and mw.col is not None:
        _dialog.push()


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
        from . import _strict_json

        path, value = _strict_json(arg)
        if path == "anki.mode":
            mw.set_theme(Theme(max(0, min(2, int(value)))))
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
