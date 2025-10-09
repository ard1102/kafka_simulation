# Sensor Pipeline Simulation: Kafka → ClickHouse → Grafana

This repo simulates how sensor events are collected, stored in a data warehouse, and analyzed with live dashboards. It’s built for learning: generate events, ingest them, and visualize real-time activity in Grafana.

## What You’ll Learn
- Simulate sensor producers streaming JSON events
- Ingest to ClickHouse via a Python consumer
- Build Grafana dashboards that feel “live” using `ingest_time`

## Quickstart
- Build and start the stack:
  - `docker compose build`
  - `docker compose up -d`
- Open Grafana: `http://localhost:3000`
- Follow consumer logs: `docker compose logs -f consumer`

## Architecture (at a glance)
- Producers read `data/sensor_data.csv`, filter by device, and publish to Kafka topic `sensor_data`.
- Consumer batches and writes rows to ClickHouse table `default.sensor_data`.
- Grafana is preprovisioned to query ClickHouse and render dashboards.
- Use `ingest_time` for “now” windows and latest reads; keep `ts` for historical grouping.

## Flow Diagram
```
[data/sensor_data.csv]
        |
        v
+-------------------+     JSON events      +-----------+
| Producers (A/B/C) | -------------------> |  Kafka    |
| filter by device  |   topic: sensor_data |  broker   |
+-------------------+                      +-----------+
                                                |
                                                v
                                         +----------------+
                                         |   Consumer     |
                                         | batch inserts  |
                                         | type mapping   |
                                         +----------------+
                                                |
                                                v
                                    +--------------------------+
                                    | ClickHouse (MergeTree)   |
                                    | table: default.sensor_data|
                                    +--------------------------+
                                                |
                                                v
                                    +--------------------------+
                                    | Grafana Dashboards       |
                                    | realtime via ingest_time |
                                    +--------------------------+
```

## Verify the Flow
- Kafka: `docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list`
- Sample messages: `docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic sensor_data --from-beginning --max-messages 10`
- ClickHouse count: `SELECT count() FROM default.sensor_data;`

## Dive Deeper
- Overview: `docs/01-project-overview.md`
- Setup & running: `docs/02-setup-and-running.md`
- Grafana dashboards & queries: `docs/05-grafana-dashboards.md`

## Contributing
PRs welcome. Keep secrets in environment variables and update docs when dashboards or schemas change.