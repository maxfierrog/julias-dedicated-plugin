"""AnkiWeb installs add-ons into `addons21/<numeric id>/`, not the folder named
in manifest.json. Code must derive its own name from `__name__` (e.g.
`mw.addonManager.addon_from_module(__name__)`), never hardcode it.
"""

from devtools import scripts


def test_no_hardcoded_package_name():
    name = scripts._package_name()
    offenders = [
        str(p.relative_to(scripts.ADDON_SRC))
        for p in scripts.ADDON_SRC.rglob("*")
        if p.is_file()
        and p.name != "manifest.json"
        and p.suffix in {".py", ".js", ".css", ".html", ".json"}
        and name in p.read_text(errors="ignore")
    ]
    assert not offenders, f"Hardcoded add-on folder name in: {offenders}"
