
import sqlite3

import alerts
import database


def test_threshold_events_are_recorded_only_on_transitions(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)
    database.initialize_database()

    thresholds = {
        "cpu_percent": 85,
        "memory_percent": 90,
        "disk_percent": 90,
    }

    def evaluate(cpu):
        metrics = {
            "cpu_percent": cpu,
            "memory_percent": 50,
            "disk_percent": 40,
        }
        return alerts.evaluate_thresholds(
            "2026-10-10T12:00:00+02:00",
            metrics,
            thresholds,
        )

    first = evaluate(90)
    second = evaluate(95)
    third = evaluate(70)
    fourth = evaluate(70)

    assert [e["event_type"] for e in first] == ["ALERT"]
    assert second == []
    assert [e["event_type"] for e in third] == ["RECOVERED"]
    assert fourth == []

    with sqlite3.connect(db_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM threshold_events"
        ).fetchone()[0]

    assert count == 2
