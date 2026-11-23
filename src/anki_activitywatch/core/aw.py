"""ActivityWatch REST shapes: bucket name, URLs and JSON bodies. No network here."""

from typing import Any
from urllib.parse import quote

from .tracker import Heartbeat

BUCKET_PREFIX = "aw-watcher-anki-activity_"
EVENT_TYPE = "app.anki.activity"
CLIENT = "anki-activitywatch"


def bucket_id(hostname: str) -> str:
    return f"{BUCKET_PREFIX}{hostname}"


def pulsetime(interval: float) -> float:
    """How far apart two identical heartbeats may be and still merge: two intervals, so one late
    heartbeat (a busy main thread, a slow request) doesn't split the event."""
    return 2 * interval


def api(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/api/0/{path.lstrip('/')}"


def bucket_url(base_url: str, bucket: str) -> str:
    return api(base_url, f"buckets/{quote(bucket, safe='')}")


def heartbeat_url(base_url: str, bucket: str, interval: float) -> str:
    return f"{bucket_url(base_url, bucket)}/heartbeat?pulsetime={pulsetime(interval):g}"


def bucket_body(hostname: str) -> dict[str, Any]:
    return {"client": CLIENT, "type": EVENT_TYPE, "hostname": hostname}


def heartbeat_body(hb: Heartbeat) -> dict[str, Any]:
    return {"timestamp": hb.timestamp.isoformat(), "duration": 0, "data": hb.context.data()}
