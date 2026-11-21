import json
import zipfile

from devtools import scripts


def test_manifest_matches_folder():
    manifest = json.loads((scripts.ADDON_SRC / "manifest.json").read_text())
    assert manifest["package"] == scripts.ADDON_SRC.name


def test_package_builds_flat_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(scripts, "DIST", tmp_path)
    scripts.package()
    with zipfile.ZipFile(tmp_path / "better_reviewer.ankiaddon") as zf:
        names = set(zf.namelist())
    assert {"__init__.py", "manifest.json", "config.json"} <= names
    assert not any("__pycache__" in n or n == "meta.json" for n in names)
