"""Reads deck names from the collection. Uses `anki` only, never `aqt`."""

from collections.abc import Sequence

from anki.collection import Collection
from anki.utils import ids2str

from .core.decks import most_common_deck


def deck_name(col: Collection, deck_id: int) -> str | None:
    if not deck_id:
        return None
    return col.decks.name_if_exists(deck_id)  # type: ignore[arg-type]


def home_deck_ids(col: Collection, card_ids: Sequence[int]) -> list[int]:
    """The deck each card lives in. A card borrowed by a filtered deck counts in its home deck,
    since the home deck is what says which class it belongs to."""
    if not card_ids:
        return []
    assert col.db is not None, "collection is closed"
    rows = col.db.list(
        f"select case when odid != 0 then odid else did end from cards where id in {ids2str(card_ids)}"
    )
    return [int(r) for r in rows]


def card_deck(col: Collection, card_id: int) -> str | None:
    ids = home_deck_ids(col, [card_id])
    return deck_name(col, ids[0]) if ids else None


def most_common_card_deck(col: Collection, card_ids: Sequence[int]) -> str | None:
    """The deck most of `card_ids` live in (ties: the name that sorts first)."""
    ids = home_deck_ids(col, card_ids)
    names = {did: deck_name(col, did) for did in set(ids)}
    return most_common_deck(names[did] for did in ids)
