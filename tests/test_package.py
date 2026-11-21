import json
import zipfile

from devtools import scripts


def test_manifest_matches_folder():
    manifest = json.loads((scripts.ADDON_SRC / "manifest.json").read_text())
    assert manifest["package"] == scripts.ADDON_SRC.name


def test_package_builds_flat_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(scripts, "DIST", tmp_path)
    scripts.package()
    with zipfile.ZipFile(tmp_path / "julias_dedicated_plugin.ankiaddon") as zf:
        names = set(zf.namelist())
    assert {"__init__.py", "manifest.json", "config.json"} <= names
    assert not any("__pycache__" in n or n == "meta.json" for n in names)


def test_version_consistent():
    from conftest import ADDON

    manifest = json.loads((ADDON / "manifest.json").read_text())
    version = (ADDON / "version.py").read_text().split('"')[1]
    assert manifest["human_version"] == version


def test_no_platform_specific_strftime_flags():
    """'%-d' / '%-I' work on macOS/Linux but raise ValueError on Windows."""
    from conftest import ADDON

    for path in ADDON.rglob("*.py"):
        assert "%-" not in path.read_text(), path.name
