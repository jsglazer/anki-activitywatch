"""The add-on's config (Anki's add-on config JSON), read with defaults so a bad value can't break Anki."""

from dataclasses import dataclass
from typing import Any

DEFAULT_URL = "http://127.0.0.1:5600"
DEFAULT_INTERVAL = 5.0
MIN_INTERVAL = 1.0
MAX_INTERVAL = 60.0


@dataclass(frozen=True)
class Settings:
    enabled: bool = True
    url: str = DEFAULT_URL
    interval: float = DEFAULT_INTERVAL


def parse(raw: dict[str, Any] | None) -> Settings:
    """Settings from the config dict; any missing or invalid value falls back to its default."""
    raw = raw or {}
    enabled = raw.get("enabled", True)
    url = raw.get("activitywatch_url", DEFAULT_URL)
    interval = raw.get("heartbeat_seconds", DEFAULT_INTERVAL)
    if not isinstance(enabled, bool):
        enabled = True
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        url = DEFAULT_URL
    if isinstance(interval, bool) or not isinstance(interval, int | float):
        interval = DEFAULT_INTERVAL
    interval = min(MAX_INTERVAL, max(MIN_INTERVAL, float(interval)))
    return Settings(enabled=enabled, url=url.rstrip("/"), interval=interval)
