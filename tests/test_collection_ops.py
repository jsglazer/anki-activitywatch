from collections.abc import Iterator
from pathlib import Path

import pytest
from anki.collection import Collection

from anki_activitywatch import collection_ops

ECON = "Class::2026B::Econ::Ch03"
DATA = "Data Concepts"


@pytest.fixture
def col(tmp_path: Path) -> Iterator[Collection]:
    c = Collection(str(tmp_path / "test.anki2"))
    yield c
    c.close()


def add_cards(col: Collection, deck: str, n: int) -> list[int]:
    did = col.decks.id(deck)
    assert did is not None
    model = col.models.by_name("Basic")
    assert model is not None
    ids = []
    for i in range(n):
        note = col.new_note(model)
        note["Front"] = f"{deck} {i}"
        col.add_note(note, did)
        ids.extend(int(c.id) for c in note.cards())
    return ids


def test_card_deck(col: Collection):
    (cid,) = add_cards(col, ECON, 1)
    assert collection_ops.card_deck(col, cid) == ECON


def test_most_common_card_deck(col: Collection):
    econ = add_cards(col, ECON, 2)
    data = add_cards(col, DATA, 3)
    assert collection_ops.most_common_card_deck(col, econ + data) == DATA
    assert collection_ops.most_common_card_deck(col, econ + data[:1]) == ECON
    assert collection_ops.most_common_card_deck(col, []) is None


def test_filtered_deck_cards_count_in_home_deck(col: Collection):
    cids = add_cards(col, ECON, 2)
    fid = col.sched.get_or_create_filtered_deck(0)
    fid.name = "Cram"
    fid.config.search_terms[0].search = f'"deck:{ECON}"'
    out = col.sched.add_or_update_filtered_deck(fid)
    assert col.db.scalar(f"select count() from cards where did = {out.id}") == 2
    assert collection_ops.card_deck(col, cids[0]) == ECON
    assert collection_ops.most_common_card_deck(col, cids) == ECON


def test_deck_name(col: Collection):
    did = col.decks.id(DATA)
    assert did is not None
    assert collection_ops.deck_name(col, int(did)) == DATA
    assert collection_ops.deck_name(col, 0) is None
    assert collection_ops.deck_name(col, 987654321) is None
