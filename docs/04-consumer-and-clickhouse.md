# Consumer and ClickHouse

The consumer reads JSON messages from Kafka, converts fields to ClickHouse-compatible types, and inserts rows in batches for efficiency.

## Consumer Configuration
- `KAFKA_BROKER` (e.g., `kafka-broker:9092`)
- `KAFKA_TOPIC` (default: `sensor_data`)
- `BATCH_SIZE` (e.g., `500`)
- `FLUSH_INTERVAL_SEC` (e.g., `2`)
- `CLICKHOUSE_HOST` (e.g., `clickhouse-server`)
- `CLICKHOUSE_USER` (e.g., `sensor`)
- `CLICKHOUSE_PASSWORD` (e.g., `sensorpass`)

## Type Mapping
From message to table columns:
- `device_id`: String
- `ts`: DateTime
- `data.co`, `data.humidity`, `data.light`, `data.lpg`, `data.smoke`, `data.temp`: Float64
- `data.motion`: UInt8
- `ingest_time`: DateTime64 (set by consumer at insert time)

## ClickHouse Schema
Create table script (`clickhouse_setup/01_init_schema.sql`):
```
CREATE TABLE IF NOT EXISTS default.sensor_data (
  device_id String,
  ts DateTime,
  co Float64,
  humidity Float64,
  light Float64,
  lpg Float64,
  motion UInt8,
  smoke Float64,
  temp Float64,
  ingest_time DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (device_id, ts);
```

## Batching and Flush
- Messages are buffered until `BATCH_SIZE` or `FLUSH_INTERVAL_SEC` is reached.
- Inserts use a single multi-row statement to reduce overhead.

## Connectivity
- ClickHouse HTTP port: `8123`
- Test: `curl http://localhost:8123/?query=SELECT%20count()%20FROM%20default.sensor_data`

## `ts` vs `ingest_time`
- `ts` reflects the original timestamp in the CSV (historical).
- `ingest_time` reflects when the consumer wrote the row.
- Grafana can use `ingest_time` for real-time windows.