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
    with urllib.request.urlopen(f"http://localhost:{PORT}/json") as r:
        return json.load(r)


def call(method: str, view: str = MAIN, **params) -> dict:
    url = next(
        (v["webSocketDebuggerUrl"] for v in views() if v["title"] == view),
        None,
    )
    if url is None:
        raise SystemExit(f"No web view titled {view!r}; is dev Anki running?")
    ws = websocket.create_connection(url, suppress_origin=True)
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


def screenshot(path: str, view: str = MAIN) -> str:
    data = call("Page.captureScreenshot", view, format="png")["data"]
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))
    return path


def screenshot_main() -> None:
    p = argparse.ArgumentParser(description="Screenshot a dev Anki web view.")
    p.add_argument("out", nargs="?", default="screenshot.png")
    p.add_argument("--view", default=MAIN)
    a = p.parse_args()
    print(screenshot(a.out, a.view))


def js_main() -> None:
    p = argparse.ArgumentParser(description="Evaluate JS in a dev Anki view.")
    p.add_argument("expr")
    p.add_argument("--view", default=MAIN)
    a = p.parse_args()
    print(json.dumps(evaluate(a.expr, a.view), indent=2, ensure_ascii=False))
