# Project Overview

This project simulates a sensor data pipeline using Docker. Three Kafka producers stream filtered sensor readings into a single topic. A Python consumer ingests these messages into ClickHouse, and Grafana visualizes the data through preprovisioned dashboards.

## Architecture
- Kafka broker (KRaft mode) hosts topic `sensor_data`.
- Producers `A`, `B`, `C` read `data/sensor_data.csv`, filter by device, and publish JSON.
- Consumer batches messages and inserts into `default.sensor_data` (ClickHouse).
- Grafana connects to ClickHouse and loads dashboards from JSON files.

## Data Flow
- Source: `data/sensor_data.csv`
- Producers: Publish JSON messages to `sensor_data`
- Consumer: Parses JSON, converts types, writes to ClickHouse
- Visualization: Grafana dashboards query ClickHouse

## Key Components
- Topic: `sensor_data`
- Producers: `producer_a`, `producer_b`, `producer_c` filtering by device IDs
- Consumer: `consumer/consumer.py` with batch insert and type conversions
- ClickHouse Table: `default.sensor_data` using `MergeTree`
- Grafana: Datasource `ClickHouse` and dashboards `sensor_overview.json`, `current_status_table.json`, `current_status_and_events.json`

## ClickHouse Schema Summary
Columns: `device_id` (String), `ts` (DateTime), `co`, `humidity`, `light`, `lpg`, `motion` (UInt8), `smoke`, `temp` (Float64), and `ingest_time` (DateTime64).

- Engine: `MergeTree`
- Order by: `(device_id, ts)`
- `ingest_time` is added on write so Grafana queries can track real-time ingestion even if `ts` from the dataset is old.

## Repository Layout
- `data/` raw CSV
- `producers/` three Kafka producers
- `consumer/` Python ClickHouse inserter
- `clickhouse_setup/` SQL schema init
- `grafana/` datasource provisioning and dashboards
- `docker-compose.yml` orchestration

## Why `ingest_time`?
Real-time dashboards require a time column that reflects when data arrived. The dataset’s `ts` may be historical. Using `ingest_time` makes Grafana’s time filter and refresh behavior align with live ingestion.