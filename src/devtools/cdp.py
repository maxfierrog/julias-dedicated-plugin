"""Drive the running dev Anki through Chromium DevTools (port 8080, enabled by
`uv run anki-dev`): evaluate JS in a web view and capture screenshots.

    uv run screenshot [out.png] [--view "main webview"]
    uv run anki-js "document.body.innerText"
"""

import argparse
import base64
import itertools
import json
import os
import urllib.request

import websocket

PORT = int(os.environ.get("QTWEBENGINE_REMOTE_DEBUGGING", "8080"))
MAIN = "main webview"
_ids = itertools.count(1)


def views() -> list[dict]:
    with urllib.request.urlopen(
        f"http://localhost:{PORT}/json", timeout=10
    ) as r:
        return json.load(r)


def call(method: str, view: str = MAIN, **params) -> dict:
    url = next(
        (v["webSocketDebuggerUrl"] for v in views() if v["title"] == view),
        None,
    )
    if url is None:
        raise SystemExit(f"No web view titled {view!r}; is dev Anki running?")
    ws = websocket.create_connection(url, suppress_origin=True, timeout=15)
    try:
        msg_id = next(_ids)
        ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == msg_id:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg["result"]
    finally:
        ws.close()


def evaluate(expr: str, view: str = MAIN):
    res = call(
        "Runtime.evaluate",
        view,
        expression=expr,
        returnByValue=True,
        awaitPromise=True,
    )
    if "exceptionDetails" in res:
        raise RuntimeError(res["exceptionDetails"])
    return res["result"].get("value")


def _capture(view: str):
    import io

    from PIL import Image

    data = call("Page.captureScreenshot", view, format="png")["data"]
    return Image.open(io.BytesIO(base64.b64decode(data)))


def screenshot(path: str, view: str = MAIN, full: bool = True, width=1600):
    """Save a PNG of one web view, or with full=True the whole main window
    (top toolbar + main view + bottom bar stacked), downscaled to `width`."""
    from PIL import Image

    names = ["top toolbar", MAIN, "bottom toolbar"] if full else [view]
    parts = []
    for n in names:
        # Collapsed bars (e.g. a hidden toolbar) can't be captured; skip them.
        visible = evaluate(
            "document.visibilityState === 'visible' && window.innerHeight >= 16"
            " && !document.body.classList.contains('hidden')",
            n,
        )
        if full and not visible:
            continue
        parts.append(_capture(n))
    w = max(p.width for p in parts)
    img = Image.new("RGB", (w, sum(p.height for p in parts)))
    y = 0
    for p in parts:
        img.paste(p, (0, y))
        y += p.height
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)))
    img.save(path)
    return path


def screenshot_main() -> None:
    p = argparse.ArgumentParser(description="Screenshot a dev Anki web view.")
    p.add_argument("out", nargs="?", default="screenshot.png")
    p.add_argument("--view", help="capture only this web view")
    a = p.parse_args()
    print(screenshot(a.out, a.view or MAIN, full=a.view is None))


def js_main() -> None:
    p = argparse.ArgumentParser(description="Evaluate JS in a dev Anki view.")
    p.add_argument("expr")
    p.add_argument("--view", default=MAIN)
    a = p.parse_args()
    print(json.dumps(evaluate(a.expr, a.view), indent=2, ensure_ascii=False))


def _wait_for(expr: str, view: str = MAIN, timeout: float = 5.0) -> None:
    import time

    end = time.time() + timeout
    while time.time() < end:
        try:
            if evaluate(expr, view):
                return
        except (RuntimeError, StopIteration, OSError):
            pass
        time.sleep(0.15)
    raise SystemExit(f"Timed out waiting for: {expr}")


def goto(target: str, deck: str = "MCAT") -> None:
    """Navigate the dev Anki via the same bridge commands its UI uses."""
    if target == "home":
        evaluate("pycmd('decks')", "top toolbar")
        _wait_for("!!document.querySelector('a.deck')")
    elif target in ("deck", "review", "answer"):
        goto("home")
        evaluate(
            "(()=>{const a=[...document.querySelectorAll('a.deck')]"
            f".find(a=>a.innerText.trim()=={json.dumps(deck)});"
            "a.click();return 1})()"
        )
        _wait_for("!!document.querySelector('#study, .congrats, h3')")
        if target in ("review", "answer"):
            evaluate("pycmd('study')")
            _wait_for("!!document.querySelector('#qa')")
            _wait_for("document.querySelector('#qa').innerText.length > 0")
        if target == "answer":
            evaluate("pycmd('ans')")
            _wait_for("!!document.querySelector('#answer')")
    else:
        raise SystemExit(f"unknown target {target!r}")


def goto_main() -> None:
    p = argparse.ArgumentParser(description="Navigate the dev Anki.")
    p.add_argument("target", choices=["home", "deck", "review", "answer"])
    p.add_argument("--deck", default="MCAT")
    p.add_argument("--shot", help="also save a screenshot to this path")
    a = p.parse_args()
    goto(a.target, a.deck)
    if a.shot:
        import time

        time.sleep(0.6)
        print(screenshot(a.shot))


def grab_main() -> None:
    """Save PNGs of every visible native Anki window (dev mode only)."""
    import glob
    import time

    p = argparse.ArgumentParser(description="Capture native Anki windows.")
    p.add_argument("folder")
    a = p.parse_args()
    folder = os.path.abspath(a.folder)
    os.makedirs(folder, exist_ok=True)
    for f in glob.glob(os.path.join(folder, "*.png")):
        os.remove(f)
    evaluate(f"pycmd({json.dumps('jdp:dev-grab:' + folder)})", "top toolbar")
    time.sleep(1.0)
    for f in sorted(glob.glob(os.path.join(folder, "*.png"))):
        print(f)
