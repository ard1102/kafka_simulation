---
title: Kafka → ClickHouse → Grafana Sensor Pipeline
description: Simulate sensor events, ingest to ClickHouse, and visualize live dashboards in Grafana.
layout: default
---

# Sensor Pipeline Simulation

Learn-by-doing: generate sensor events, store them in a warehouse (ClickHouse), and analyze in Grafana with live dashboards.

## Quickstart
- Build and start:
  - `docker compose build`
  - `docker compose up -d`
- Open Grafana: `http://localhost:3000`
- Tail consumer logs: `docker compose logs -f consumer`

## Flow
```
CSV → Producers (A/B/C) → Kafka topic `sensor_data` → Consumer → ClickHouse → Grafana
```

## Highlights
- Real-time views via `ingest_time`; keep `ts` for historical grouping
- Auto-provisioned Grafana datasource and dashboards
- ClickHouse `default.sensor_data` with MergeTree engine

## Docs
- Overview: `01-project-overview.md`
- Setup & Running: `02-setup-and-running.md`
- Producers & Schema: `03-producers-message-schema.md`
- Consumer & ClickHouse: `04-consumer-and-clickhouse.md`
- Dashboards: `05-grafana-dashboards.md`

## Repo
- GitHub: https://github.com/ard1102/kafka_simulation