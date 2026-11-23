"""anki-activitywatch: reports the deck you are working in to ActivityWatch. Entry point: registers hooks."""

from aqt import mw

if mw is not None:  # None when imported outside Anki (tests, type checks)
    from .ui.addon import setup

    addon = setup(mw, __name__)
