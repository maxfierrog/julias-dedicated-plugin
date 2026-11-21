"""macOS: blend the window's title bar into the theme.

Qt doesn't expose this, so we talk to AppKit through the Objective-C runtime
with ctypes (Anki doesn't bundle PyObjC). We make the title bar transparent,
paint the window background in the theme's canvas color, and hide the title
text, so the traffic-light buttons sit on the same surface as the app.

Everything is best-effort: any failure leaves the stock title bar.
"""

import ctypes
import ctypes.util
import sys

_objc = None


def _runtime():
    global _objc
    if _objc is None:
        lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        lib.objc_getClass.restype = ctypes.c_void_p
        lib.objc_getClass.argtypes = [ctypes.c_char_p]
        lib.sel_registerName.restype = ctypes.c_void_p
        lib.sel_registerName.argtypes = [ctypes.c_char_p]
        _objc = lib
    return _objc


def _send(restype, receiver, selector: str, *args):
    """objc_msgSend with an exact signature (required on arm64)."""
    objc = _runtime()
    argtypes = [ctypes.c_void_p, ctypes.c_void_p] + [type(a) for a in args]
    fn = ctypes.CFUNCTYPE(restype, *argtypes)(
        ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
    )
    return fn(receiver, objc.sel_registerName(selector.encode()), *args)


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))


NS_WINDOW_TITLE_HIDDEN = 1


def blend_title_bar(widget, hex_color: str) -> bool:
    """Make `widget`'s native window title bar match `hex_color`."""
    if sys.platform != "darwin":
        return False
    view = ctypes.c_void_p(int(widget.winId()))
    window = _send(ctypes.c_void_p, view, "window")
    if not window:
        return False
    window = ctypes.c_void_p(window)
    _send(None, window, "setTitlebarAppearsTransparent:", ctypes.c_bool(True))
    _send(
        None,
        window,
        "setTitleVisibility:",
        ctypes.c_long(NS_WINDOW_TITLE_HIDDEN),
    )
    r, g, b = _hex_to_rgb(hex_color)
    ns_color = _runtime().objc_getClass(b"NSColor")
    color = _send(
        ctypes.c_void_p,
        ctypes.c_void_p(ns_color),
        "colorWithSRGBRed:green:blue:alpha:",
        ctypes.c_double(r),
        ctypes.c_double(g),
        ctypes.c_double(b),
        ctypes.c_double(1.0),
    )
    _send(None, window, "setBackgroundColor:", ctypes.c_void_p(color))
    return True


def describe(widget) -> dict:
    """Read the window's title-bar state back from AppKit (for diagnostics)."""
    view = ctypes.c_void_p(int(widget.winId()))
    window = ctypes.c_void_p(_send(ctypes.c_void_p, view, "window"))
    return {
        "transparent": bool(
            _send(ctypes.c_bool, window, "titlebarAppearsTransparent")
        ),
        "title_visibility": _send(ctypes.c_long, window, "titleVisibility"),
    }


def restore_title_bar(widget) -> bool:
    if sys.platform != "darwin":
        return False
    view = ctypes.c_void_p(int(widget.winId()))
    window = _send(ctypes.c_void_p, view, "window")
    if not window:
        return False
    window = ctypes.c_void_p(window)
    _send(None, window, "setTitlebarAppearsTransparent:", ctypes.c_bool(False))
    _send(None, window, "setTitleVisibility:", ctypes.c_long(0))
    return True
