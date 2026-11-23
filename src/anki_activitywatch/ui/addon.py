"""Wires the tracker to Anki: a timer plus the GUI hooks that signal a change, and a Tools menu entry."""

import logging
from datetime import UTC, datetime

from aqt import gui_hooks
from aqt.main import AnkiQt
from aqt.qt import QAction, QTimer, QWidget, qconnect
from aqt.utils import showInfo

from ..aw_client import AWClient
from ..core import settings as settings_mod
from ..core.settings import Settings
from ..core.tracker import Context, Tracker
from .window_context import current_context

log = logging.getLogger(__name__)


class Addon:
    def __init__(self, mw: AnkiQt, module: str) -> None:
        self.mw = mw
        self.module = module
        self.settings: Settings = settings_mod.parse(mw.addonManager.getConfig(module))
        self.tracker = Tracker(self.settings.interval)
        self.client = AWClient(self.settings.url, self.settings.interval)
        self.timer = QTimer(mw)
        qconnect(self.timer.timeout, self.tick)

    # -- lifecycle ----------------------------------------------------------------------------------

    def register(self) -> None:
        gui_hooks.profile_did_open.append(self.start)
        gui_hooks.profile_will_close.append(self.stop)
        gui_hooks.reviewer_did_show_question.append(lambda *_: self.soon())
        gui_hooks.state_did_change.append(lambda *_: self.soon())
        gui_hooks.browser_did_change_row.append(lambda *_: self.soon())
        gui_hooks.add_cards_did_change_deck.append(lambda *_: self.soon())
        gui_hooks.focus_did_change.append(self._on_focus)
        self.mw.addonManager.setConfigUpdatedAction(self.module, self._on_config)
        action = QAction("ActivityWatch status", self.mw)
        qconnect(action.triggered, self.show_status)
        self.mw.form.menuTools.addAction(action)

    def start(self) -> None:
        if not self.settings.enabled:
            return
        self.client.start()
        self.timer.start(int(self.settings.interval * 1000))
        self.soon()

    def stop(self) -> None:
        self.timer.stop()
        self._send(None)  # end the current event now
        self.client.stop()

    # -- updates ------------------------------------------------------------------------------------

    def soon(self) -> None:
        """Re-check after the current event finishes, so the window shows its new state first."""
        if self.timer.isActive():
            QTimer.singleShot(0, self.tick)

    def tick(self) -> None:
        try:
            context = current_context(self.mw)
        except Exception:  # an add-on bug must never surface as an Anki error
            log.debug("anki-activitywatch: could not read the Anki context", exc_info=True)
            context = None
        self._send(context)

    def _send(self, context: Context | None) -> None:
        for hb in self.tracker.update(context, datetime.now(UTC)):
            self.client.submit(hb)

    def _on_focus(self, new: QWidget | None, old: QWidget | None) -> None:
        if new is None or old is None or new.window() is not old.window():
            self.soon()

    def _on_config(self, raw: dict[str, object]) -> None:
        self.stop()
        self.settings = settings_mod.parse(raw)
        self.tracker = Tracker(self.settings.interval)
        self.client = AWClient(self.settings.url, self.settings.interval)
        if self.mw.col is not None:
            self.start()

    # -- Tools menu ---------------------------------------------------------------------------------

    def show_status(self) -> None:
        s = self.client.status()
        when = s.last_ok.astimezone().strftime("%H:%M:%S") if s.last_ok else "never"
        last = s.last_sent.context.data() if s.last_sent else None
        lines = [
            f"Reporting: {'on' if self.settings.enabled else 'off (config: enabled)'}",
            f"ActivityWatch: {self.settings.url}",
            f"Bucket: {s.bucket or '(not yet created or checked)'}",
            f"Last heartbeat accepted: {when}",
            f"Last data: {last}",
            f"Now: {self.tracker.current.data() if self.tracker.current else 'nothing to report'}",
            f"Last error: {s.last_error or 'none'}",
            f"Heartbeats dropped: {s.dropped}",
        ]
        showInfo("\n".join(lines), title="anki-activitywatch")


def setup(mw: AnkiQt, module: str) -> Addon:
    addon = Addon(mw, module)
    addon.register()
    return addon
