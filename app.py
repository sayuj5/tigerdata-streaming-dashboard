import os
import random
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import psycopg2
from dotenv import load_dotenv
import streamlit as st


load_dotenv()

SENSORS = ["sensor-1", "sensor-2", "sensor-3"]
METRIC_BASELINES = {
    "sensor-1": {"temperature": 21.5, "humidity": 46.0, "pressure": 1012.0},
    "sensor-2": {"temperature": 23.0, "humidity": 52.0, "pressure": 1010.0},
    "sensor-3": {"temperature": 19.0, "humidity": 58.0, "pressure": 1014.0},
}


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is not set.")
    return psycopg2.connect(database_url)


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS iot_sensors (
                time TIMESTAMPTZ NOT NULL,
                sensor_id TEXT NOT NULL,
                temperature DOUBLE PRECISION NOT NULL,
                humidity DOUBLE PRECISION NOT NULL,
                pressure DOUBLE PRECISION NOT NULL
            );
            """
        )
        cur.execute(
            """
            SELECT create_hypertable(
                'iot_sensors',
                'time',
                if_not_exists => TRUE
            );
            """
        )
    conn.commit()


def generate_sensor_row(sensor_id):
    baseline = METRIC_BASELINES[sensor_id]
    return (
        datetime.now(timezone.utc),
        sensor_id,
        round(baseline["temperature"] + random.uniform(-2.0, 2.0), 2),
        round(max(0.0, min(100.0, baseline["humidity"] + random.uniform(-5.0, 5.0))), 2),
        round(baseline["pressure"] + random.uniform(-4.0, 4.0), 2),
    )


def insert_sensor_data(conn):
    rows = [generate_sensor_row(sensor_id) for sensor_id in SENSORS]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO iot_sensors (time, sensor_id, temperature, humidity, pressure)
            VALUES (%s, %s, %s, %s, %s);
            """,
            rows,
        )
    conn.commit()


def fetch_latest_rows(conn, limit=100):
    query = """
        SELECT time, sensor_id, temperature, humidity, pressure
        FROM iot_sensors
        ORDER BY time DESC
        LIMIT %s;
    """
    dataframe = pd.read_sql_query(query, conn, params=(limit,))
    if not dataframe.empty:
        dataframe = dataframe.sort_values("time")
    return dataframe


def render_chart(dataframe, metric):
    figure = px.line(
        dataframe,
        x="time",
        y=metric,
        color="sensor_id",
        markers=True,
        title=f"{metric.capitalize()} trend by sensor",
    )
    st.plotly_chart(figure, use_container_width=True)


def main():
    st.set_page_config(page_title="IoT Sensor Dashboard", layout="wide")
    st.title("Real-time IoT Sensor Streaming Analytics Dashboard")
    st.caption("Streaming data from sensor-1, sensor-2, and sensor-3 into TimescaleDB")
    st.markdown("<meta http-equiv='refresh' content='5'>", unsafe_allow_html=True)

    try:
        with get_connection() as conn:
            ensure_schema(conn)
            insert_sensor_data(conn)
            latest_rows = fetch_latest_rows(conn, limit=100)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Unable to load data: {exc}")
        return

    st.subheader("Latest 100 rows")
    st.dataframe(latest_rows, use_container_width=True)

    if latest_rows.empty:
        st.info("No sensor data available yet.")
        return

    chart_col_1, chart_col_2 = st.columns(2)
    with chart_col_1:
        render_chart(latest_rows, "temperature")
    with chart_col_2:
        render_chart(latest_rows, "humidity")

    st.subheader("Pressure")
    render_chart(latest_rows, "pressure")


if __name__ == "__main__":
    main()
