"""Headless smoke test: the pinned `anki` library can drive a collection.

This is the pattern for testing add-on logic that only needs pylib (notes,
cards, review logs) without launching the GUI.
"""

from anki.collection import Collection


def test_add_and_review_basic_note(tmp_path):
    col = Collection(str(tmp_path / "collection.anki2"))
    try:
        note = col.new_note(col.models.by_name("Basic"))
        note["Front"] = "Which amino acid is achiral?"
        note["Back"] = "Glycine"
        col.add_note(note, col.decks.id("Default"))

        card = col.sched.getCard()
        assert card is not None
        assert "Glycine" in card.answer()
        col.sched.answerCard(card, 3)
        assert col.card_count() == 1
    finally:
        col.close()
