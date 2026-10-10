
import argparse
from email import parser
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "checksystem.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def show_metrics(limit):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT timestamp, cpu_percent, memory_percent,
                   disk_percent, disk_free_gb
            FROM system_metrics
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    if not rows:
        print("Nessuna metrica registrata.")
        return

    print(f"\nUltime {len(rows)} rilevazioni")
    print("-" * 90)

    for row in reversed(rows):
        print(
            f"{row['timestamp']} | "
            f"CPU {row['cpu_percent']:5.1f}% | "
            f"RAM {row['memory_percent']:5.1f}% | "
            f"Disco {row['disk_percent']:5.1f}% | "
            f"Liberi {row['disk_free_gb']:.2f} GB"
        )


def show_stats(hours):
    with get_connection() as connection:
        row = connection.execute("""
            SELECT
                COUNT(*) AS samples,
                AVG(cpu_percent) AS avg_cpu,
                MAX(cpu_percent) AS max_cpu,
                AVG(memory_percent) AS avg_memory,
                MAX(memory_percent) AS max_memory,
                AVG(disk_percent) AS avg_disk
            FROM system_metrics
            WHERE datetime(timestamp) >=
                  datetime('now', ?)
        """, (f"-{hours} hours",)).fetchone()

    print(f"\nStatistiche ultime {hours} ore")
    print("-" * 40)
    print(f"Rilevazioni: {row['samples']}")

    if row["samples"] == 0:
        print("Non ci sono dati in questo intervallo.")
        return

    print(f"CPU media: {row['avg_cpu']:.1f}%")
    print(f"CPU massima: {row['max_cpu']:.1f}%")
    print(f"RAM media: {row['avg_memory']:.1f}%")
    print(f"RAM massima: {row['max_memory']:.1f}%")
    print(f"Disco utilizzato medio: {row['avg_disk']:.1f}%")


def show_services(hours):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                service_name,
                COUNT(*) AS checks,
                SUM(
                    CASE WHEN status != 'UP' THEN 1 ELSE 0 END
                ) AS failures,
                AVG(response_ms) AS avg_response,
                MAX(timestamp) AS last_check
            FROM service_checks
            WHERE datetime(timestamp) >=
                  datetime('now', ?)
            GROUP BY service_name
            ORDER BY service_name
        """, (f"-{hours} hours",)).fetchall()

    print(f"\nReport servizi - ultime {hours} ore")
    print("-" * 75)

    if not rows:
        print("Nessun controllo registrato in questo intervallo.")
        return

    for row in rows:
        failures = row["failures"] or 0
        checks = row["checks"]
        availability = (checks - failures) / checks * 100

        avg = row["avg_response"]
        avg_text = f"{avg:.1f} ms" if avg is not None else "N/D"

        print(f"\nServizio: {row['service_name']}")
        print(f"Controlli: {checks}")
        print(f"Controlli falliti: {failures}")
        print(f"Successo dei controlli: {availability:.1f}%")
        print(f"Tempo medio di risposta: {avg_text}")
        print(f"Ultimo controllo: {row['last_check']}")


def show_events(limit):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT timestamp, service_name, event_type,
                   previous_status, current_status, details
            FROM service_events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    print("\nEventi recenti")
    print("-" * 75)

    if not rows:
        print("Nessun evento registrato.")
        return

    for row in rows:
        print(
            f"{row['timestamp']} | "
            f"{row['service_name']} | "
            f"{row['event_type']} | "
            f"{row['previous_status'] or 'N/D'}"
            f" -> {row['current_status']}"
        )

        if row["details"]:
            print(f"  Dettaglio: {row['details']}")


def show_threshold_events(limit=20):
    from database import get_connection

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT timestamp, metric, event_type, value, threshold, details
            FROM threshold_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    if not rows:
        print("Nessun avviso di soglia registrato.")
        return

    for row in rows:
        print(
            f"{row['timestamp']} | "
            f"{row['event_type']} | "
            f"{row['details']}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="CheckSystem - Storico e report"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    metrics_parser = subparsers.add_parser(
        "metrics",
        help="Mostra le ultime metriche",
    )
    metrics_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Numero di rilevazioni da mostrare",
    )

    stats_parser = subparsers.add_parser(
        "stats",
        help="Mostra le statistiche del sistema",
    )
    stats_parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Intervallo temporale in ore",
    )

    services_parser = subparsers.add_parser(
        "services",
        help="Mostra il report dei servizi",
    )
    services_parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Intervallo temporale in ore",
    )

    events_parser = subparsers.add_parser(
    "events",
    help="Mostra le interruzioni e i ripristini",
    )
    events_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Numero massimo di eventi",
    )

    threshold_parser = subparsers.add_parser(
    "thresholds",
    help="Mostra gli avvisi e i ripristini delle soglie",
    )
    threshold_parser.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if not DATABASE_PATH.exists():
        parser.error(
            "Database non trovato. Avvia prima python main.py."
        )

    if args.command == "metrics":
        if args.limit < 1:
            parser.error("--limit deve essere almeno 1.")
        show_metrics(args.limit)

    elif args.command == "stats":
        if args.hours < 1:
            parser.error("--hours deve essere almeno 1.")
        show_stats(args.hours)

    elif args.command == "services":
        if args.hours < 1:
            parser.error("--hours deve essere almeno 1.")
        show_services(args.hours)

    elif args.command == "events":
        if args.limit < 1:
            parser.error("--limit deve essere almeno 1.")
        show_events(args.limit)
    
    elif args.command == "thresholds":
        if args.limit < 1:
            parser.error("--limit deve essere almeno 1.")
        show_threshold_events(args.limit)

if __name__ == "__main__":
    main()
