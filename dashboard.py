
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=5000, key="checksystem_refresh")

DB_PATH = Path(__file__).resolve().parent / "checksystem.db"

st.set_page_config(
    page_title="CheckSystem Dashboard",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=5)
def load_data():
    with sqlite3.connect(DB_PATH) as connection:
        metrics = pd.read_sql_query("""
            SELECT timestamp, cpu_percent, memory_percent,
                   disk_percent, disk_free_gb
            FROM system_metrics
            ORDER BY id DESC
            LIMIT 1000
        """, connection)

        services = pd.read_sql_query("""
            SELECT timestamp, service_name, url, status,
                   status_code, response_ms, error
            FROM service_checks
            ORDER BY id DESC
            LIMIT 1000
        """, connection)

    if not metrics.empty:
        metrics = metrics.iloc[::-1].copy()
        metrics["timestamp"] = pd.to_datetime(
            metrics["timestamp"], utc=True
        )

    if not services.empty:
        services["timestamp"] = pd.to_datetime(
            services["timestamp"], utc=True
        )

    return metrics, services


DATABASE_PATH = Path(__file__).resolve().parent / "checksystem.db"


@st.cache_data(ttl=5)
def load_threshold_events(limit=100):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT timestamp, metric, event_type,
                   value, threshold, details
            FROM threshold_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return pd.DataFrame([dict(row) for row in rows])


@st.cache_data(ttl=5)
def load_active_thresholds():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT e.timestamp, e.metric, e.value,
                   e.threshold, e.details
            FROM threshold_events AS e
            INNER JOIN (
                SELECT metric, MAX(id) AS latest_id
                FROM threshold_events
                GROUP BY metric
            ) AS latest ON e.id = latest.latest_id
            WHERE e.event_type = 'ALERT'
            ORDER BY e.id DESC
            """
        ).fetchall()

    return pd.DataFrame([dict(row) for row in rows])


st.title("CheckSystem Dashboard")
st.caption("System and Service Monitoring")

if not DB_PATH.exists():
    st.warning("Database non trovato. Avvia prima python main.py.")
    st.stop()

metrics, services = load_data()

if metrics.empty:
    st.info("In attesa delle prime rilevazioni.")
    st.stop()

latest = metrics.iloc[-1]

col1, col2, col3 = st.columns(3)

col1.metric("CPU", f"{latest['cpu_percent']:.1f}%")
col2.metric("RAM", f"{latest['memory_percent']:.1f}%")
col3.metric("Disco utilizzato", f"{latest['disk_percent']:.1f}%")

st.subheader("Risorse di sistema")

chart_data = metrics.set_index("timestamp")[
    ["cpu_percent", "memory_percent", "disk_percent"]
]

st.line_chart(chart_data)

st.subheader("Spazio disponibile")

st.metric(
    "Spazio libero",
    f"{latest['disk_free_gb']:.2f} GB",
)

st.subheader("Stato dei servizi")

if services.empty:
    st.info("Nessun controllo dei servizi registrato.")
else:
    latest_services = (
        services.sort_values("timestamp")
        .groupby("service_name", as_index=False)
        .tail(1)
        .sort_values("service_name")
    )

    st.dataframe(
        latest_services[
            ["service_name", "status", "status_code",
             "response_ms", "timestamp", "error"]
        ],
        hide_index=True,
        use_container_width=True,
    )

    failures = int((services["status"] != "UP").sum())
    st.metric(
        "Controlli falliti nello storico caricato",
        failures,
    )

    st.subheader("Tempi di risposta")

    response_data = services.dropna(
        subset=["response_ms"]
    ).sort_values("timestamp")

    if not response_data.empty:
        response_chart = response_data.pivot_table(
            index="timestamp",
            columns="service_name",
            values="response_ms",
            aggfunc="last",
        )

        st.line_chart(response_chart)
st.divider()
st.header("Avvisi di sistema")

active_alerts = load_active_thresholds()

if active_alerts.empty:
    st.success("Nessun avviso di soglia attivo.")
else:
    st.warning(f"Avvisi attivi: {len(active_alerts)}")

    for _, alert in active_alerts.iterrows():
        st.markdown(
            f"**{alert['metric']}** — "
            f"{alert['value']:.1f}% "
            f"(soglia: {alert['threshold']:.1f}%)"
        )
        st.caption(
            f"Dal {alert['timestamp']} · {alert['details']}"
        )

st.subheader("Storico avvisi e ripristini")

events = load_threshold_events(limit=100)

if events.empty:
    st.info("Non sono ancora presenti eventi di soglia.")
else:
    st.dataframe(
        events,
        use_container_width=True,
        hide_index=True,
    )


st.caption(
    "I grafici mostrano al massimo le ultime 1000 rilevazioni "
    "disponibili nel database."
)

if st.button("Aggiorna dati"):
    st.cache_data.clear()
    st.rerun()

st.caption(
    "I dati si aggiornano dalla cache ogni 5 secondi "
    "quando la pagina viene rieseguita."
)




