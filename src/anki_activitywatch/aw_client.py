"""Sends heartbeats to the local ActivityWatch server on a background thread.

Nothing here may ever reach Anki's user: every network error is caught, logged at debug level and
remembered for the status window. The queue is bounded and `submit` never blocks, so a stopped or
slow ActivityWatch can't slow Anki down. After a failure the client waits `retry_seconds` before
trying again and drops heartbeats meanwhile (they would only describe the past few seconds).
"""

import contextlib
import json
import logging
import queue
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .core import aw
from .core.tracker import Heartbeat

log = logging.getLogger(__name__)

# (method, url, json body or None, timeout) -> parsed JSON response (None for an empty body)
Fetch = Callable[[str, str, Any, float], Any]


def urllib_fetch(method: str, url: str, body: Any, timeout: float) -> Any:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data, {"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


@dataclass
class Status:
    bucket: str | None = None
    last_sent: Heartbeat | None = None
    last_ok: datetime | None = None
    last_error: str | None = None
    dropped: int = 0


class AWClient:
    def __init__(
        self,
        base_url: str,
        interval: float,
        fetch: Fetch = urllib_fetch,
        clock: Callable[[], float] = time.monotonic,
        timeout: float = 2.0,
        retry_seconds: float = 15.0,
        max_queue: int = 50,
    ) -> None:
        self.base_url = base_url
        self.interval = interval
        self._fetch = fetch
        self._clock = clock
        self._timeout = timeout
        self._retry_seconds = retry_seconds
        self._queue: queue.Queue[Heartbeat | None] = queue.Queue(max_queue)
        self._lock = threading.Lock()
        self._status = Status()
        self._retry_at = 0.0
        self._thread: threading.Thread | None = None

    # -- called from Anki's main thread -------------------------------------------------------------

    def start(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="anki-activitywatch", daemon=True)
            self._thread.start()

    def stop(self, wait: float = 1.0) -> None:
        if self._thread is None:
            return
        with contextlib.suppress(queue.Full):  # daemon thread; it ends with Anki anyway
            self._queue.put_nowait(None)
        self._thread.join(wait)
        self._thread = None

    def submit(self, hb: Heartbeat) -> None:
        """Queue a heartbeat. Never blocks; drops it if the queue is full."""
        try:
            self._queue.put_nowait(hb)
        except queue.Full:
            with self._lock:
                self._status.dropped += 1

    def status(self) -> Status:
        with self._lock:
            return Status(**vars(self._status))

    # -- worker -------------------------------------------------------------------------------------

    def _run(self) -> None:
        while True:
            hb = self._queue.get()
            if hb is None:
                return
            self.process(hb)

    def process(self, hb: Heartbeat) -> bool:
        """Send one heartbeat, creating the bucket first if needed. True if ActivityWatch took it."""
        if self._clock() < self._retry_at:
            with self._lock:
                self._status.dropped += 1
            return False
        try:
            bucket = self._ensure_bucket()
            self._fetch(
                "POST",
                aw.heartbeat_url(self.base_url, bucket, self.interval),
                aw.heartbeat_body(hb),
                self._timeout,
            )
        except (OSError, ValueError, KeyError, TypeError) as e:  # URLError/HTTPError are OSErrors
            log.debug("ActivityWatch heartbeat failed: %s", e)
            self._retry_at = self._clock() + self._retry_seconds
            with self._lock:
                self._status.bucket = None  # check the bucket again once ActivityWatch is back
                self._status.last_error = f"{type(e).__name__}: {e}"
            return False
        with self._lock:
            self._status.last_sent = hb
            self._status.last_ok = hb.timestamp
            self._status.last_error = None
        return True

    def _ensure_bucket(self) -> str:
        with self._lock:
            known = self._status.bucket
        if known:
            return known
        host = self._fetch("GET", aw.api(self.base_url, "info"), None, self._timeout)["hostname"]
        bucket = aw.bucket_id(str(host))
        existing = self._fetch("GET", aw.api(self.base_url, "buckets/"), None, self._timeout) or {}
        if bucket not in existing:
            try:
                self._fetch(
                    "POST", aw.bucket_url(self.base_url, bucket), aw.bucket_body(str(host)), self._timeout
                )
            except urllib.error.HTTPError as e:
                if e.code != 304:  # 304 = created meanwhile by another call
                    raise
        with self._lock:
            self._status.bucket = bucket
        return bucket
