
import sqlite3

import database


def test_database_creates_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    database.initialize_database()

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """)
        }

    assert "system_metrics" in tables
    assert "service_checks" in tables
    assert "service_events" in tables


def test_metrics_are_saved(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    database.initialize_database()

    metrics = {
        "cpu_percent": 25.0,
        "memory_percent": 60.0,
        "memory_used_gb": 8.0,
        "disk_percent": 70.0,
        "disk_free_gb": 100.0,
    }

    database.save_metrics("2026-10-10T12:00:00+02:00", metrics)

    with sqlite3.connect(db_path) as connection:
        row = connection.execute("""
            SELECT cpu_percent, memory_percent
            FROM system_metrics
        """).fetchone()

    assert row == (25.0, 60.0)


def test_service_events_only_record_transitions(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    database.initialize_database()

    def save(timestamp, status):
        result = {
            "name": "Test Service",
            "status": status,
            "status_code": 200 if status == "UP" else None,
            "response_ms": 100.0 if status == "UP" else None,
            "error": "Connection failed" if status == "DOWN" else None,
        }

        database.save_service_check(
            timestamp,
            result,
            "https://example.com",
        )

    save("2026-10-10T12:00:00+02:00", "UP")
    save("2026-10-10T12:00:10+02:00", "DOWN")
    save("2026-10-10T12:00:20+02:00", "DOWN")
    save("2026-10-10T12:00:30+02:00", "UP")

    with sqlite3.connect(db_path) as connection:
        checks = connection.execute(
            "SELECT COUNT(*) FROM service_checks"
        ).fetchone()[0]

        events = connection.execute("""
            SELECT event_type
            FROM service_events
            ORDER BY id
        """).fetchall()

    assert checks == 4
    assert events == [("FAILED",), ("RECOVERED",)]
