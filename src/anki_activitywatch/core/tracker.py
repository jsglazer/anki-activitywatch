"""Turns "what Anki is showing now" into the heartbeats ActivityWatch should get.

ActivityWatch merges a heartbeat into the previous event when the data is identical and it arrives
within `pulsetime` of that event's end. So while the context stays the same, one heartbeat every
`interval` seconds keeps a single growing event. When the context changes, the old event is first
extended to the moment of the change, then the new context starts a new event at that same moment,
so consecutive events meet without a gap or an overlap.
"""

from dataclasses import dataclass
from datetime import datetime

ACTIVITIES = ("review", "browse", "add", "edit", "overview", "decks")


@dataclass(frozen=True)
class Context:
    """What the focused Anki window is doing: one of ACTIVITIES, and the deck (None if unknown)."""

    activity: str
    deck: str | None

    def __post_init__(self) -> None:
        if self.activity not in ACTIVITIES:
            raise ValueError(f"unknown activity {self.activity!r}")

    def data(self) -> dict[str, str | None]:
        return {"deck": self.deck, "activity": self.activity}


@dataclass(frozen=True)
class Heartbeat:
    timestamp: datetime
    context: Context


class Tracker:
    """Decides when to send a heartbeat. Holds only the last context and when it was last sent."""

    def __init__(self, interval: float) -> None:
        if interval <= 0:
            raise ValueError("interval must be positive")
        self.interval = interval
        self._current: Context | None = None
        self._last_sent: datetime | None = None

    @property
    def current(self) -> Context | None:
        return self._current

    def update(self, context: Context | None, now: datetime) -> list[Heartbeat]:
        """Report the current context (None = no Anki window to report) at time `now`."""
        if context == self._current:
            if context is None or self._last_sent is None:
                return []
            if (now - self._last_sent).total_seconds() < self.interval:
                return []
            self._last_sent = now
            return [Heartbeat(now, context)]

        out: list[Heartbeat] = []
        if self._current is not None:
            out.append(Heartbeat(now, self._current))  # close the old event at the change
        if context is not None:
            out.append(Heartbeat(now, context))
        self._current = context
        self._last_sent = now
        return out
