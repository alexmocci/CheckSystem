
import json
import time
from datetime import datetime

import psutil
import requests

from alerts import evaluate_thresholds
from logging_config import configure_logging
from notifications import send_telegram_notification

logger = configure_logging()
from database import (
    initialize_database,
    save_metrics,
    save_service_check,
)



def load_config():
    with open("config.json", "r", encoding="utf-8") as file:
        return json.load(file)


def get_system_metrics(disk_path):
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(disk_path)

    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": memory.percent,
        "memory_used_gb": memory.used / (1024 ** 3),
        "disk_percent": disk.percent,
        "disk_free_gb": disk.free / (1024 ** 3),
    }


def check_service(service):
    started = time.perf_counter()

    try:
        response = requests.get(
            service["url"],
            timeout=5,
        )

        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000

        return {
            "name": service["name"],
            "status": (
                "UP"
                if response.status_code < 400
                else "ERROR"
            ),
            "status_code": response.status_code,
            "response_ms": round(elapsed_ms, 2),
        }

    except requests.RequestException as error:
        return {
            "name": service["name"],
            "status": "DOWN",
            "error": str(error),
        }


def main():
    config = load_config()

    interval = config["interval_seconds"]
    disk_path = config["disk_path"]
    services = config["services"]
    thresholds = config["thresholds"]

    initialize_database()

    print("CheckSystem - System Monitor")
    print("Database SQLite inizializzato.")
    print("Premi Ctrl+C per terminare.\n")
    logger.info("CheckSystem avviato")

    try:
        while True:
            timestamp = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )

            metrics = get_system_metrics(disk_path)

            save_metrics(timestamp, metrics)

            print(f"\n[{timestamp}]")
            print(
                f"CPU: {metrics['cpu_percent']:.1f}%"
            )
            print(
                f"RAM: {metrics['memory_percent']:.1f}% "
                f"({metrics['memory_used_gb']:.2f} GB)"
            )
            print(
                f"Disco: {metrics['disk_percent']:.1f}% "
                f"- Liberi: {metrics['disk_free_gb']:.2f} GB"
            )
            logger.info(
                        "Metriche rilevate: CPU=%.1f%% RAM=%.1f%% Disco=%.1f%%",
                        metrics["cpu_percent"],
                        metrics["memory_percent"],
                        metrics["disk_percent"],
                        )
            print("\nServizi:")

            for service in services:
                result = check_service(service)

                save_service_check(
                    timestamp,
                    result,
                    service["url"],
                )

                if result["status"] == "DOWN":
                    print(
                        f"  [DOWN] {result['name']} - "
                        f"{result['error']}"
                    )
                else:
                    print(
                        f"  [{result['status']}] "
                        f"{result['name']} - "
                        f"HTTP {result['status_code']} - "
                        f"{result['response_ms']} ms"
                    )

            events = evaluate_thresholds(timestamp, metrics, thresholds)

            for event in events:
                print(f"[{event['event_type']}] {event['details']}")
                if event["event_type"] == "ALERT":
                    logger.warning("%s", event["details"])
                else:
                    logger.info("%s", event["details"])
                sent = send_telegram_notification(event)

                if not sent:
                    print(
                        f"Notifica non inviata per "
                        f"{event['metric']}: verifica la configurazione Telegram."
                    )
                    
            print("\nDati salvati nel database.")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nMonitoraggio terminato.")


if __name__ == "__main__":
    main()
