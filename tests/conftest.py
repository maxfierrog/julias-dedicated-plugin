import importlib.util
import sys
from pathlib import Path

import pytest
from anki.collection import Collection

from devtools.seed import build
from devtools.seed.simulate import simulate

ADDON = Path(__file__).resolve().parents[1] / "src" / "julias_dedicated_plugin"


def load_addon_module(name: str):
    """Import a GUI-free add-on module (e.g. stats, settings, theme) without
    running the package __init__, which needs a running Anki."""
    spec = importlib.util.spec_from_file_location(
        f"jdp_{name}", ADDON / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def seeded_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("seeded") / "collection.anki2"
    col = Collection(str(path))
    hard = build(col)
    simulate(col, days=90, seed=3, hard_nids=hard)
    col.close()
    return path


@pytest.fixture
def seeded_col(seeded_path, tmp_path):
    """A private copy of the seeded collection per test."""
    copy = tmp_path / "collection.anki2"
    copy.write_bytes(seeded_path.read_bytes())
    col = Collection(str(copy))
    yield col
    col.close()
