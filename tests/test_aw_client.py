import urllib.error
from datetime import UTC, datetime
from typing import Any

from anki_activitywatch.aw_client import AWClient
from anki_activitywatch.core.tracker import Context, Heartbeat

BASE = "http://aw.test"
HB = Heartbeat(datetime(2026, 11, 23, 12, 0, tzinfo=UTC), Context("review", "Class::2026B::Econ::Ch03"))
BUCKET = "aw-watcher-anki-activity_MBA24.local"


class FakeAW:
    """Records calls; answers like aw-server. Set `down` to make every call fail."""

    def __init__(self, buckets: dict[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, str, Any]] = []
        self.buckets = dict(buckets or {})
        self.down = False

    def __call__(self, method: str, url: str, body: Any, timeout: float) -> Any:
        self.calls.append((method, url, body))
        if self.down:
            raise urllib.error.URLError("connection refused")
        if url.endswith("/api/0/info"):
            return {"hostname": "MBA24.local"}
        if url.endswith("/api/0/buckets/"):
            return self.buckets
        if method == "POST" and url.endswith(f"/buckets/{BUCKET}"):
            self.buckets[BUCKET] = body
            return None
        return None


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def make(fake: FakeAW, clock: Clock | None = None, **kw: Any) -> AWClient:
    return AWClient(BASE, 5, fetch=fake, clock=clock or Clock(), **kw)


def test_creates_bucket_then_sends_heartbeat():
    fake = FakeAW()
    assert make(fake).process(HB)
    methods = [(m, u.removeprefix(BASE)) for m, u, _ in fake.calls]
    assert methods == [
        ("GET", "/api/0/info"),
        ("GET", "/api/0/buckets/"),
        ("POST", f"/api/0/buckets/{BUCKET}"),
        ("POST", f"/api/0/buckets/{BUCKET}/heartbeat?pulsetime=10"),
    ]
    assert fake.calls[-1][2]["data"] == {"deck": "Class::2026B::Econ::Ch03", "activity": "review"}


def test_existing_bucket_is_not_recreated_and_is_checked_once():
    fake = FakeAW({BUCKET: {}})
    c = make(fake)
    c.process(HB)
    c.process(HB)
    posts = [u for m, u, _ in fake.calls if m == "POST"]
    assert posts == [f"{BASE}/api/0/buckets/{BUCKET}/heartbeat?pulsetime=10"] * 2
    assert sum(u.endswith("/info") for _, u, _ in fake.calls) == 1
    assert c.status().bucket == BUCKET
    assert c.status().last_ok == HB.timestamp


def test_failure_is_silent_and_backs_off():
    fake, clock = FakeAW(), Clock()
    fake.down = True
    c = make(fake, clock, retry_seconds=15)
    assert c.process(HB) is False
    assert "URLError" in (c.status().last_error or "")
    n = len(fake.calls)
    clock.t = 10
    assert c.process(HB) is False  # still backing off: no network call
    assert len(fake.calls) == n
    assert c.status().dropped == 1
    fake.down = False
    clock.t = 15
    assert c.process(HB) is True
    assert c.status().last_error is None


def test_bucket_is_rechecked_after_a_failure():
    fake, clock = FakeAW(), Clock()
    c = make(fake, clock)
    c.process(HB)
    fake.down = True
    c.process(HB)
    fake.down, clock.t = False, 100
    fake.calls.clear()
    c.process(HB)
    assert fake.calls[0][1].endswith("/api/0/info")


def test_bucket_conflict_304_is_fine():
    class Exists(FakeAW):
        def __call__(self, method: str, url: str, body: Any, timeout: float) -> Any:
            if method == "POST" and url.endswith(f"/buckets/{BUCKET}"):
                raise urllib.error.HTTPError(url, 304, "Not Modified", None, None)  # type: ignore[arg-type]
            return super().__call__(method, url, body, timeout)

    assert make(Exists()).process(HB)


def test_bad_response_is_caught():
    def broken(method: str, url: str, body: Any, timeout: float) -> Any:
        return {}  # no "hostname"

    c = AWClient(BASE, 5, fetch=broken, clock=Clock())
    assert c.process(HB) is False
    assert "KeyError" in (c.status().last_error or "")


def test_submit_never_blocks_and_counts_drops():
    c = make(FakeAW(), max_queue=2)
    for _ in range(5):
        c.submit(HB)  # no worker running: the queue fills
    assert c.status().dropped == 3


def test_worker_thread_sends_and_stops():
    fake = FakeAW({BUCKET: {}})
    c = make(fake)
    c.start()
    c.submit(HB)
    c.stop(wait=5)
    assert any(u.endswith("pulsetime=10") for _, u, _ in fake.calls)
