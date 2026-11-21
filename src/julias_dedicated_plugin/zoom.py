"""Zoom for the main window: ⌘+/⌘= in, ⌘− out, ⌘0 reset.

Anki's View → Zoom In/Out have no shortcuts and only scale the middle web
view, so the toolbar and bottom bar stayed small. We scale all three
together and remember the level per profile (per computer, since the right
size depends on the screen)."""

from aqt import mw
from aqt.qt import QKeySequence

PROFILE_KEY = "jdp_zoom"
STEP, LOW, HIGH = 0.1, 0.5, 2.0


def _views():
    return (mw.web, mw.toolbarWeb, mw.bottomWeb)


def current() -> float:
    return float(mw.pm.profile.get(PROFILE_KEY, 1.0)) if mw.pm.profile else 1.0


def apply(factor: float | None = None) -> None:
    factor = round(
        min(HIGH, max(LOW, current() if factor is None else factor)), 2
    )
    if mw.pm.profile is not None:
        mw.pm.profile[PROFILE_KEY] = factor
    for view in _views():
        view.setZoomFactor(factor)
    # The bars size themselves to their content; re-measure after scaling
    # (but don't re-expand a bar Anki has auto-hidden).
    for bar in (mw.toolbarWeb, mw.bottomWeb):
        if not getattr(bar, "hidden", False):
            bar.adjustHeightToFit()


def _make_bars_zoom_aware() -> None:
    """Anki sizes the toolbar and bottom bar to their content's height in
    CSS pixels, which ignores zoom, so zoomed-in bars got clipped. Scale
    those measurements by the zoom factor, for every future re-measure too."""
    for view in (mw.toolbarWeb, mw.bottomWeb):
        if getattr(view, "_jdp_zoom_aware", False):
            continue
        view._jdp_zoom_aware = True
        on_height = view._onHeight  # bound original

        def scaled(q, f=on_height, v=view):
            f(round(q * v.zoomFactor()) if q else q)
            # Anki also uses web_height to offset reviewer background images
            # inside the (already zoomed) main view: keep it unscaled.
            if q and hasattr(v, "web_height"):
                v.web_height = int(q)

        view._onHeight = scaled
        if hasattr(view, "animate_height"):
            animate = view.animate_height
            view.animate_height = lambda h, f=animate, v=view: f(
                round(h * v.zoomFactor()) if h and h > 1 else h
            )


def install() -> None:
    _make_bars_zoom_aware()
    m = mw.form
    for action, key, fn in (
        (
            m.actionZoomIn,
            [
                QKeySequence(QKeySequence.StandardKey.ZoomIn),
                QKeySequence("Ctrl+="),
            ],
            lambda: apply(current() + STEP),
        ),
        (
            m.actionZoomOut,
            [QKeySequence(QKeySequence.StandardKey.ZoomOut)],
            lambda: apply(current() - STEP),
        ),
        (m.actionResetZoom, [QKeySequence("Ctrl+0")], lambda: apply(1.0)),
    ):
        try:
            action.triggered.disconnect()  # Anki's main-view-only handlers
        except TypeError:
            pass
        action.setShortcuts(key)
        action.triggered.connect(fn)
