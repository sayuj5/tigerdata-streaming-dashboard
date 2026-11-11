# tigerdata-streaming-dashboard

Real-time IoT sensor streaming analytics dashboard using Python, Streamlit, and TimescaleDB.

## Features

- Simulates 3 IoT sensors (`sensor-1`, `sensor-2`, `sensor-3`)
- Streams temperature, humidity, and pressure data into PostgreSQL/TimescaleDB
- Creates/uses a hypertable named `iot_sensors`
- Fetches and displays the latest 100 rows
- Renders interactive Plotly line charts with automatic refresh

## Setup

1. Clone the repository.
2. Copy environment variables:

   ```bash
   cp .env.example .env
   ```

3. Update `DATABASE_URL` in `.env` to point to your PostgreSQL/TimescaleDB instance.
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run the dashboard

```bash
streamlit run app.py
```

The app refreshes automatically every 5 seconds and appends new simulated sensor points on each refresh.
