
import database


METRIC_LABELS = {
    "cpu_percent": "CPU",
    "memory_percent": "RAM",
    "disk_percent": "Disco",
}


def evaluate_thresholds(timestamp, metrics, thresholds):
    """Registra gli avvisi e i ripristini senza duplicare gli eventi."""

    created_events = []

    with database.get_connection() as connection:
        for metric, threshold in thresholds.items():
            if metric not in metrics:
                continue

            value = metrics[metric]
            label = METRIC_LABELS.get(metric, metric)

            previous = connection.execute(
                """
                SELECT event_type
                FROM threshold_events
                WHERE metric = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (metric,),
            ).fetchone()

            is_active = (
                previous is not None
                and previous["event_type"] == "ALERT"
            )

            if value >= threshold and not is_active:
                event_type = "ALERT"
                details = (
                    f"{label} al {value:.1f}% "
                    f"(soglia: {threshold:.1f}%)"
                )

            elif value < threshold and is_active:
                event_type = "RECOVERED"
                details = (
                    f"{label} rientrato al {value:.1f}% "
                    f"(soglia: {threshold:.1f}%)"
                )

            else:
                continue

            connection.execute(
                """
                INSERT INTO threshold_events
                    (timestamp, metric, event_type, value, threshold, details)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    metric,
                    event_type,
                    value,
                    threshold,
                    details,
                ),
            )

            created_events.append({
                "timestamp": timestamp,
                "metric": metric,
                "event_type": event_type,
                "value": value,
                "threshold": threshold,
                "details": details,
            })

    return created_events
