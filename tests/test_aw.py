from datetime import UTC, datetime

from anki_activitywatch.core import aw
from anki_activitywatch.core.tracker import Context, Heartbeat


def test_bucket_name_matches_concept():
    assert aw.bucket_id("MBA24.local") == "aw-watcher-anki-activity_MBA24.local"


def test_urls():
    base = "http://127.0.0.1:5600/"
    assert aw.api(base, "info") == "http://127.0.0.1:5600/api/0/info"
    assert (
        aw.heartbeat_url(base, "aw-watcher-anki-activity_MBA24.local", 5)
        == "http://127.0.0.1:5600/api/0/buckets/aw-watcher-anki-activity_MBA24.local/heartbeat?pulsetime=10"
    )
    assert aw.heartbeat_url(base, "b", 2.5).endswith("pulsetime=5")


def test_bodies():
    hb = Heartbeat(datetime(2026, 11, 23, 12, 0, 1, tzinfo=UTC), Context("add", "Data Concepts"))
    assert aw.heartbeat_body(hb) == {
        "timestamp": "2026-11-23T12:00:01+00:00",
        "duration": 0,
        "data": {"deck": "Data Concepts", "activity": "add"},
    }
    assert aw.bucket_body("h") == {
        "client": "anki-activitywatch",
        "type": "app.anki.activity",
        "hostname": "h",
    }
