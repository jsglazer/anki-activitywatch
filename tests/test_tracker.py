from datetime import UTC, datetime, timedelta

import pytest

from anki_activitywatch.core.tracker import Context, Heartbeat, Tracker

T0 = datetime(2026, 11, 23, 12, 0, 0, tzinfo=UTC)
ECON = Context("review", "Class::2026B::Econ::Ch03")
DATA = Context("browse", "Data Concepts")


def at(seconds: float) -> datetime:
    return T0 + timedelta(seconds=seconds)


def test_first_context_sends_one_heartbeat():
    t = Tracker(5)
    assert t.update(ECON, at(0)) == [Heartbeat(at(0), ECON)]


def test_same_context_waits_for_interval():
    t = Tracker(5)
    t.update(ECON, at(0))
    assert t.update(ECON, at(4.9)) == []
    assert t.update(ECON, at(5)) == [Heartbeat(at(5), ECON)]
    assert t.update(ECON, at(9)) == []
    assert t.update(ECON, at(10)) == [Heartbeat(at(10), ECON)]


def test_change_closes_old_then_opens_new_at_same_moment():
    t = Tracker(5)
    t.update(ECON, at(0))
    assert t.update(DATA, at(2)) == [Heartbeat(at(2), ECON), Heartbeat(at(2), DATA)]
    assert t.current == DATA
    assert t.update(DATA, at(6)) == []  # interval restarts at the change
    assert t.update(DATA, at(7)) == [Heartbeat(at(7), DATA)]


def test_deck_change_within_same_activity_is_a_change():
    t = Tracker(5)
    t.update(ECON, at(0))
    calc = Context("review", "Math::Calculus")
    assert t.update(calc, at(1)) == [Heartbeat(at(1), ECON), Heartbeat(at(1), calc)]


def test_none_closes_event_and_stays_quiet():
    t = Tracker(5)
    t.update(ECON, at(0))
    assert t.update(None, at(3)) == [Heartbeat(at(3), ECON)]
    assert t.update(None, at(30)) == []
    assert t.update(ECON, at(31)) == [Heartbeat(at(31), ECON)]


def test_nothing_before_any_context():
    assert Tracker(5).update(None, at(0)) == []


def test_unknown_deck_is_reported_as_none():
    assert Context("browse", None).data() == {"deck": None, "activity": "browse"}


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        Context("sleeping", "A")
    with pytest.raises(ValueError):
        Tracker(0)
