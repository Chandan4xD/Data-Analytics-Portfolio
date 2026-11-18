from datetime import datetime, timedelta

from ct import alerts


def test_first_alert_is_sent():
    assert alerts.should_send(None, datetime(2026, 1, 1), 24)


def test_duplicate_inside_cooldown_is_blocked():
    now = datetime(2026, 1, 2, 12)
    assert not alerts.should_send(now - timedelta(hours=3), now, 24)


def test_alert_after_cooldown_is_sent():
    now = datetime(2026, 1, 2, 12)
    assert alerts.should_send(now - timedelta(hours=25), now, 24)
