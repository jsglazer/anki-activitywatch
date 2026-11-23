from anki_activitywatch.core.settings import DEFAULT_URL, Settings, parse


def test_defaults():
    assert parse(None) == Settings()
    assert parse({}) == Settings(enabled=True, url=DEFAULT_URL, interval=5.0)


def test_valid_values():
    s = parse({"enabled": False, "activitywatch_url": "http://localhost:5666/", "heartbeat_seconds": 10})
    assert s == Settings(enabled=False, url="http://localhost:5666", interval=10.0)


def test_invalid_values_fall_back():
    s = parse({"enabled": "yes", "activitywatch_url": "ftp://x", "heartbeat_seconds": "fast"})
    assert s == Settings()
    assert parse({"heartbeat_seconds": True}).interval == 5.0


def test_interval_is_clamped():
    assert parse({"heartbeat_seconds": 0}).interval == 1.0
    assert parse({"heartbeat_seconds": 3600}).interval == 60.0
