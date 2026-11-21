"""`uv run seed`: build a realistic premed collection in the dev profile.

`uv run simulate` instead adds history to whatever is already in the dev
profile (e.g. a real deck imported through Anki's File → Import).
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from anki.collection import Collection
from anki.models import NotetypeDict

from devtools.scripts import DEV_BASE
from . import content, media
from .simulate import simulate

PROFILE = "User 1"


def _profile_dir() -> Path:
    return DEV_BASE / PROFILE


def _anki_running_on_dev_base() -> bool:
    out = subprocess.run(
        ["pgrep", "-fl", "Anki"], capture_output=True, text=True
    ).stdout
    return str(DEV_BASE) in out


def _add_mcat_cloze_notetype(col: Collection) -> NotetypeDict:
    mm = col.models
    nt = mm.new(content.MCAT_CLOZE)
    nt["type"] = 1  # cloze
    for name in (
        "Text",
        "Extra",
        "Lecture Notes",
        "Missed Questions",
        "Source",
    ):
        mm.add_field(nt, mm.new_field(name))
    tmpl = mm.new_template("Cloze")
    tmpl["qfmt"] = content.MCAT_CLOZE_FRONT
    tmpl["afmt"] = content.MCAT_CLOZE_BACK
    mm.add_template(nt, tmpl)
    nt["css"] = content.MCAT_CLOZE_CSS
    mm.add(nt)
    return mm.by_name(content.MCAT_CLOZE)


def build(col: Collection) -> set[int]:
    """Add notes, decks and media. Returns the ids of notes marked hard."""
    _add_mcat_cloze_notetype(col)
    for name, render in media.FIGURES.items():
        col.media.write_data(name, render().encode())

    hard: set[int] = set()
    for spec in content.NOTES:
        note = col.new_note(col.models.by_name(spec.notetype))
        for k, v in spec.fields.items():
            note[k] = v
        note.tags = list(spec.tags)
        col.add_note(note, col.decks.id(spec.deck))
        if spec.hard:
            hard.add(note.id)
    return hard


def _parse(argv, desc):
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--days", type=int, default=120, help="days of history")
    p.add_argument("--seed", type=int, default=0, help="random seed")
    return p.parse_args(argv)


def _require_closed():
    if _anki_running_on_dev_base():
        sys.exit("Quit the dev Anki first (it holds the collection open).")


def _summarize(col: Collection, sim) -> None:
    today = col.sched.today
    due = col.db.scalar(
        "select count() from cards where queue = 2 and due <= ?", today
    )
    print(
        f"{col.note_count()} notes, {col.card_count()} cards; "
        f"{len(sim.revlog)} reviews over {sim.days} days; "
        f"{due} reviews due today; {len(sim.leech_nids)} leech notes"
    )


def main(argv=None) -> None:
    args = _parse(argv, "Rebuild the dev profile's collection from scratch.")
    _require_closed()
    pdir = _profile_dir()
    if pdir.exists():
        shutil.rmtree(pdir)
    pdir.mkdir(parents=True)
    col = Collection(str(pdir / "collection.anki2"))
    try:
        hard = build(col)
        sim = simulate(col, days=args.days, seed=args.seed, hard_nids=hard)
    finally:
        col.close()
    col = Collection(str(pdir / "collection.anki2"))
    try:
        _summarize(col, sim)
    finally:
        col.close()
    print(f"Seeded {pdir}. Launch with `uv run anki-dev`.")


def simulate_main(argv=None) -> None:
    args = _parse(argv, "Add review history to the dev profile's collection.")
    _require_closed()
    path = _profile_dir() / "collection.anki2"
    if not path.exists():
        sys.exit(f"No collection at {path}; run `uv run anki-dev` once first.")
    col = Collection(str(path))
    try:
        sim = simulate(col, days=args.days, seed=args.seed)
    finally:
        col.close()
    col = Collection(str(path))
    try:
        _summarize(col, sim)
    finally:
        col.close()
