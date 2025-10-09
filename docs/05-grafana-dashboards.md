# Grafana Dashboards

Grafana is preprovisioned to connect to ClickHouse and load dashboards that visualize sensor activity.

## Access
- URL: `http://localhost:3000`
- Admin credentials via env (e.g., `GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`).

## Datasource
Provisioned in `grafana/provisioning/datasources/clickhouse.yml`:
- Type: `grafana-clickhouse-datasource`
- Host: `http://clickhouse-server:8123`
- Auth: `sensor/sensorpass`
- Default DB: `default`

## Dashboards
Auto-loaded from `grafana/dashboards/`:
- `sensor_overview.json`: Stats, time series for temp & humidity, device event counts, templated `device_id`.
- `current_status_table.json`: Table of latest status across sensors; per-sensor queries for `ts`, `temp`, `device_id`.
- `current_status_and_events.json`: Recent events table for last 24 hours.

## Query Patterns
Prefer `ingest_time` for real-time windows:
- Events per second:
  - `SELECT toStartOfSecond(ingest_time) AS time, device_id, count() FROM default.sensor_data WHERE $__timeFilter(ingest_time) AND device_id='...' GROUP BY time, device_id ORDER BY time;`
- Temperature & Humidity over time (templated by device):
  - `SELECT ingest_time AS t, temp AS temperature, humidity AS humidity FROM default.sensor_data WHERE $__timeFilter(ingest_time) AND device_id='${device_id:text}' ORDER BY ingest_time;`

Use `ts` when analyzing the data’s original timeline:
- `SELECT ts, temp, humidity FROM default.sensor_data WHERE $__timeFilter(ts) AND device_id='...' ORDER BY ts;`

## Troubleshooting
- No data appearing: Confirm consumer is running and ClickHouse has rows.
- Stale charts: Switch queries to filter on `ingest_time`.
- Datasource errors: Verify ClickHouse is reachable at `clickhouse-server:8123` from Grafana.