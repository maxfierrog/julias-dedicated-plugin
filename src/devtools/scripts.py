"""Development helpers for the Better Reviewer add-on.

All Anki state used during development lives in ``.anki-dev/`` at the repo
root (passed to Anki via ``--base``), so experiments never touch a real
collection in ``~/Library/Application Support/Anki2``.
"""

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDON_SRC = ROOT / "src" / "better_reviewer"
DEV_BASE = ROOT / ".anki-dev"
DIST = ROOT / "dist"
ANKI_BIN = Path(
    os.environ.get("ANKI_BIN", "/Applications/Anki.app/Contents/MacOS/Anki")
)

# Files that must never ship inside the .ankiaddon archive. Anki generates
# meta.json itself (it holds the user's config), and caches are local junk.
EXCLUDE_NAMES = {"meta.json", "__pycache__", ".DS_Store"}


def _package_name() -> str:
    manifest = json.loads((ADDON_SRC / "manifest.json").read_text())
    return manifest["package"]


def _addon_link() -> Path:
    return DEV_BASE / "addons21" / _package_name()


def link() -> None:
    """Symlink the add-on source into the dev profile's addons21 folder."""
    target = _addon_link()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        if target.is_symlink() and target.resolve() == ADDON_SRC:
            print(f"Already linked: {target} -> {ADDON_SRC}")
            return
        sys.exit(f"Refusing to replace existing {target}; run `unlink` first.")
    target.symlink_to(ADDON_SRC, target_is_directory=True)
    print(f"Linked {target} -> {ADDON_SRC}")


def unlink() -> None:
    """Remove the dev symlink (never deletes source files)."""
    target = _addon_link()
    if target.is_symlink():
        target.unlink()
        print(f"Unlinked {target}")
    else:
        print(f"No symlink at {target}")


def run() -> None:
    """Launch the installed Anki against the isolated dev base folder.

    Extra CLI args are forwarded to Anki (e.g. `uv run anki-dev -p Test`).
    Web views can be inspected at http://localhost:8080 in a Chromium browser.
    """
    if not ANKI_BIN.exists():
        sys.exit(f"Anki not found at {ANKI_BIN}; set ANKI_BIN.")
    link()
    env = {
        **os.environ,
        "ANKIDEV": "1",
        "QTWEBENGINE_REMOTE_DEBUGGING": os.environ.get(
            "QTWEBENGINE_REMOTE_DEBUGGING", "8080"
        ),
    }
    cmd = [str(ANKI_BIN), "--base", str(DEV_BASE), *sys.argv[1:]]
    sys.exit(subprocess.call(cmd, env=env))


def package() -> None:
    """Build dist/<package>.ankiaddon, installable by double-clicking."""
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{_package_name()}.ankiaddon"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ADDON_SRC.rglob("*")):
            rel = path.relative_to(ADDON_SRC)
            if path.is_dir() or EXCLUDE_NAMES.intersection(rel.parts):
                continue
            # Archive root must be the add-on's contents, not its folder.
            zf.write(path, rel.as_posix())
    print(f"Built {out}")
