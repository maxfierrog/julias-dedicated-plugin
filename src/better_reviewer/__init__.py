"""Better Reviewer: an Anki add-on that improves the review experience.

Anki imports this package at startup (from ``addons21/better_reviewer``), so
module-level code runs inside the GUI process. Keep it to hook registration;
do real work in the hooks.
"""

from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import showInfo

from .version import __version__

log = mw.addonManager.get_logger(__name__)


def _show_about() -> None:
    showInfo(f"Better Reviewer {__version__} is loaded.")


def _on_main_window_init() -> None:
    action = QAction("Better Reviewer: About", mw)
    action.triggered.connect(_show_about)
    mw.form.menuTools.addAction(action)
    log.info("Better Reviewer %s loaded", __version__)


gui_hooks.main_window_did_init.append(_on_main_window_init)
