"""Choosing one deck name to report when several cards are involved."""

from collections import Counter
from collections.abc import Iterable


def most_common_deck(names: Iterable[str | None]) -> str | None:
    """The deck that appears most often among `names`, ignoring None.

    Ties go to the name that sorts first, so the answer never depends on selection order.
    Returns None when there is no name at all.
    """
    counts = Counter(n for n in names if n)
    if not counts:
        return None
    best = max(counts.values())
    return min(n for n, c in counts.items() if c == best)
