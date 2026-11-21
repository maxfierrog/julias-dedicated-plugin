"""Julia's Dedicated Plugin: a personal, maintained Anki study suite.

Anki imports this package at startup from ``addons21/<folder>``, where the
folder is the manifest's package name for file installs but a numeric ID for
AnkiWeb installs (so never hardcode it). Module-level code runs inside the GUI
process: keep it to hook registration and do real work in the hooks.
"""

from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import showInfo

from .version import __version__

log = mw.addonManager.get_logger(__name__)


def _show_about() -> None:
    showInfo(f"Julia's Dedicated Plugin {__version__} is loaded.")


def _on_main_window_init() -> None:
    action = QAction("Julia's Dedicated Plugin: About", mw)
    action.triggered.connect(_show_about)
    mw.form.menuTools.addAction(action)
    log.info("Julia's Dedicated Plugin %s loaded", __version__)


gui_hooks.main_window_did_init.append(_on_main_window_init)
