"""`uv run install-addon <code> [<code> ...]`: install AnkiWeb add-ons into
the dev profile, the same way Anki's Tools → Add-ons → Get Add-ons does
(download by code, unpack into `addons21/<code>/`, record meta.json).

Useful for comparing against, or testing alongside, popular add-ons without
touching a real Anki install. Quit the dev Anki first; it reads add-ons only
at startup.
"""

import io
import json
import re
import shutil
import sys
import urllib.request
import zipfile
from urllib.parse import parse_qs, urlparse

from devtools.scripts import DEV_BASE

ANKI_POINT_VERSION = 260904  # 26.09.4; AnkiWeb picks the matching branch
URL = "https://ankiweb.net/shared/download/{}?v=2.1&p={}"


def install(code: int) -> str:
    req = urllib.request.Request(
        URL.format(code, ANKI_POINT_VERSION),
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        disposition = resp.headers.get("content-disposition", "")
        match = re.match(r"attachment; filename=(.+)", disposition)
        if resp.status != 200 or not match:
            raise RuntimeError(f"AnkiWeb has no compatible download for {code}")
        data = resp.read()
        query = parse_qs(urlparse(resp.url).query)

    name = re.sub(r"\.ankiaddon$|\.zip$", "", match.group(1).strip('"'))
    name = name.replace("_", " ").strip() or str(code)
    dest = DEV_BASE / "addons21" / str(code)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.namelist():
            target = (dest / member).resolve()
            if member.endswith("/") or not target.is_relative_to(dest):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(member))

    meta = {"name": name, "disabled": False}
    for key, q in (
        ("mod", "t"),
        ("min_point_version", "minpt"),
        ("max_point_version", "maxpt"),
        ("branch_index", "bidx"),
    ):
        if q in query:
            meta[key] = int(query[q][0])
    meta_path = dest / "meta.json"
    if meta_path.exists():  # keep any config shipped in the archive
        meta = {**json.loads(meta_path.read_text()), **meta}
    meta_path.write_text(json.dumps(meta))
    return name


def main() -> None:
    codes = sys.argv[1:]
    if not codes:
        sys.exit("usage: uv run install-addon <code> [<code> ...]")
    failed = False
    for code in codes:
        try:
            print(f"{code}: installed {install(int(code))!r}")
        except Exception as e:  # report and keep going
            failed = True
            print(f"{code}: FAILED ({e})")
    sys.exit(1 if failed else 0)
