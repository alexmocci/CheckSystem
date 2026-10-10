
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "checksystem.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cpu_percent REAL NOT NULL,
                memory_percent REAL NOT NULL,
                memory_used_gb REAL NOT NULL,
                disk_percent REAL NOT NULL,
                disk_free_gb REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS service_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service_name TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                status_code INTEGER,
                response_ms REAL,
                error TEXT
            );
            CREATE TABLE IF NOT EXISTS service_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service_name TEXT NOT NULL,
                url TEXT NOT NULL,
                event_type TEXT NOT NULL,
                previous_status TEXT,
                current_status TEXT NOT NULL,
                details TEXT
            );
            
            CREATE TABLE IF NOT EXISTS threshold_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric TEXT NOT NULL,
                event_type TEXT NOT NULL,
                value REAL NOT NULL,
                threshold REAL NOT NULL,
                details TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_threshold_events_timestamp
            ON threshold_events(timestamp);


            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON service_events(timestamp);

            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
            ON system_metrics(timestamp);

            CREATE INDEX IF NOT EXISTS idx_checks_timestamp
            ON service_checks(timestamp);
        """)


def save_metrics(timestamp, metrics):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO system_metrics (
                timestamp,
                cpu_percent,
                memory_percent,
                memory_used_gb,
                disk_percent,
                disk_free_gb
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            metrics["cpu_percent"],
            metrics["memory_percent"],
            metrics["memory_used_gb"],
            metrics["disk_percent"],
            metrics["disk_free_gb"],
        ))



def save_service_check(timestamp, result, url):
    with get_connection() as connection:
        previous = connection.execute("""
            SELECT status
            FROM service_checks
            WHERE service_name = ?
            ORDER BY id DESC
            LIMIT 1
        """, (result["name"],)).fetchone()

        previous_status = (
            previous["status"] if previous else None
        )
        current_status = result["status"]

        connection.execute("""
            INSERT INTO service_checks (
                timestamp,
                service_name,
                url,
                status,
                status_code,
                response_ms,
                error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            result["name"],
            url,
            current_status,
            result.get("status_code"),
            result.get("response_ms"),
            result.get("error"),
        ))

        event_type = None

        if previous_status is None and current_status != "UP":
            event_type = "FAILED"
        elif previous_status == "UP" and current_status != "UP":
            event_type = "FAILED"
        elif previous_status != "UP" and current_status == "UP":
            if previous_status is not None:
                event_type = "RECOVERED"

        if event_type:
            connection.execute("""
                INSERT INTO service_events (
                    timestamp,
                    service_name,
                    url,
                    event_type,
                    previous_status,
                    current_status,
                    details
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                result["name"],
                url,
                event_type,
                previous_status,
                current_status,
                result.get("error"),
            ))

