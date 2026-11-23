"""Works out which Anki window has focus and what it is showing."""

from typing import Any

from aqt.addcards import NewAddCards
from aqt.addcards_legacy import AddCards
from aqt.browser.browser import Browser
from aqt.editcurrent import NewEditCurrent
from aqt.editcurrent_legacy import EditCurrent
from aqt.main import AnkiQt
from aqt.qt import QApplication, QWidget

from .. import collection_ops
from ..core.tracker import Context


def current_context(mw: AnkiQt) -> Context | None:
    """The context of the focused Anki window, or None when Anki isn't in front, no collection is
    open, or the focused window isn't one we report (preferences, statistics, card info, …)."""
    col = mw.col
    if col is None:
        return None
    window: QWidget | None = QApplication.activeWindow()
    if window is None:
        return None

    if isinstance(window, Browser):
        return Context("browse", collection_ops.most_common_card_deck(col, list(window.selected_cards())))
    if isinstance(window, AddCards):
        return Context("add", collection_ops.deck_name(col, int(window.deck_chooser.selected_deck_id)))
    if isinstance(window, NewAddCards):
        # The experimental editor keeps its deck in the web view; the current deck is the closest guess.
        return Context("add", collection_ops.deck_name(col, int(col.decks.get_current_id())))
    if isinstance(window, EditCurrent | NewEditCurrent):
        card: Any = getattr(window.editor, "card", None)
        return Context("edit", collection_ops.card_deck(col, int(card.id)) if card is not None else None)
    if window is mw:
        return _main_window_context(mw)
    return None


def _main_window_context(mw: AnkiQt) -> Context | None:
    col = mw.col
    assert col is not None
    if mw.state == "review":
        card = mw.reviewer.card
        return Context("review", collection_ops.card_deck(col, int(card.id)) if card is not None else None)
    if mw.state == "overview":
        return Context("overview", collection_ops.deck_name(col, int(col.decks.get_current_id())))
    if mw.state == "deckBrowser":
        return Context("decks", collection_ops.deck_name(col, int(col.decks.get_current_id())))
    return None
