import subprocess
import sys

from devtools.scripts import ROOT


def test_no_undefined_names_or_broken_imports():
    """The add-on only runs inside Anki, so an undefined name (e.g. after a
    refactor) would otherwise surface only at startup. Pyflakes rules catch
    that statically."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select",
            "F",
            "--no-cache",
            str(ROOT / "src"),
            str(ROOT / "tests"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
