import re

from conftest import ADDON


def test_stylesheets_are_well_formed():
    """Catch broken CSS (e.g. a rule pasted into a selector list), which
    silently drops styles in the app."""
    for path in (ADDON / "web").glob("*.css"):
        css = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
        depth = 0
        for ch in css:
            depth += ch == "{"
            depth -= ch == "}"
            assert depth >= 0, f"unbalanced braces in {path.name}"
        assert depth == 0, f"unbalanced braces in {path.name}"
        # Every selector list must end in a selector, not a comma.
        assert not re.search(r",\s*\{", css), f"dangling comma in {path.name}"
        for sel in re.findall(r"(?:^|})\s*([^{}@]+)\{", css):
            assert sel.strip(), f"empty selector in {path.name}"
