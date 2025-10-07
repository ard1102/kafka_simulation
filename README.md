# Sensor Producer + Kafka Simulation (KRaft)

Containerized sensor data producers that read from data/sensor_data.csv and publish JSON events to a Kafka topic (sensor_data). The stack runs a single-node Kafka (KRaft mode) via Docker Compose and three producer services for different device IDs.

## Overview
- Three producers: producer_A.py, producer_B.py, producer_C.py (each targets a specific device ID)
- Publishes to Kafka topic sensor_data using kafka-python
- Configurable row limit via ROW_LIMIT (integer or all)
- Lightweight image built from python:3.11-slim; dependencies: pandas, kafka-python
- KRaft-enabled Kafka broker (no Zookeeper) with auto topic creation enabled

## Project Structure
`
.
 data/
    sensor_data.csv
 producers/
    dockerfile
    producer_A.py
    producer_B.py
    producer_C.py
 consumer/
    Dockerfile
    consumer.py
    requirements.txt
 entrypoint.sh
 docker-compose.yml
 requirements.txt
 README.md
`

## Prerequisites
- Docker Desktop installed and running
- Docker Compose v2 (use docker compose; v1 commands shown as alternatives)

## Installation
- Ensure Docker Desktop is running and Docker Compose v2 is available (`docker compose version`).
- Build the sensor producer image (used by all three producer services):
```
docker build -t sensor-producer -f ./producers/dockerfile .
```
Notes:
- The image includes `producers/`, `data/`, and `entrypoint.sh`.
- Default env baked into the image: `PRODUCER=producer_A.py`, `ROW_LIMIT=10` (overridden by Compose).

## Quick Start
  - Start the full stack (Kafka, producers, ClickHouse, consumer):
  ```
  docker compose up -d
  ```
  - Check service status and health:
  ```
  docker compose ps
  ```
  - Schema creation is automatic via ClickHouse init scripts; no manual table creation needed.
  - Observe consumer logs:
  ```
  docker logs -f consumer
  ```

Tips:
- If producers briefly start in `[DRY-RUN]` mode, restart them once Kafka is healthy:
```
docker compose restart producer-a producer-b producer-c
```
- Consumer logs can be buffered; for unbuffered output, configure the command to `python -u consumer.py` in Compose and recreate the container.

## Run via Docker Compose (End-to-End)
From the project root:
```
docker compose up -d
```
List services and ports:
```
docker compose ps
```
Follow logs for all services:
```
docker compose logs -f
```
Stop the stack:
```
docker compose down
```

## ClickHouse Table Schema
Schema is managed by ClickHouse init scripts (`clickhouse_setup/01_init_schema.sql`). The table definition is:

```
CREATE TABLE IF NOT EXISTS default.sensor_data (
  device_id String,
  ts        DateTime64(3),
  co        Float64,
  humidity  Float64,
  light     UInt8,
  lpg       Float64,
  motion    UInt8,
  smoke     Float64,
  temp      Float64
) ENGINE = MergeTree
ORDER BY (device_id, ts);
```

Notes:
- Timestamps (`ts`) are parsed as UTC and inserted as `DateTime64(3)`.
- Boolean-like fields (`light`, `motion`) are stored as `UInt8` (0/1).

## Build Producer Image
From repository root:
`
docker build -t sensor-producer -f .\producers\dockerfile .
`

Notes:
- The build copies producers/, data/, and entrypoint.sh into the image
- Default envs baked into the image: PRODUCER=producer_A.py, ROW_LIMIT=10

## Compose Reference
- Start stack: `docker compose up -d`
- View logs: `docker compose logs -f`
- List services: `docker compose ps`
- Stop stack: `docker compose down`

## Kafka Broker (KRaft) Settings
- Image: confluentinc/cp-kafka:7.8.3
- Advertised listeners: PLAINTEXT://kafka:9092 (reachable within the compose network)
- Controller listener: CONTROLLER://0.0.0.0:9093
- Auto topic creation enabled: KAFKA_AUTO_CREATE_TOPICS_ENABLE=true

## Producer Services
Compose brings up three services (producer-a, producer-b, producer-c) that share the same image and vary by PRODUCER env:

- Common environment:
  - KAFKA_BROKER=kafka:9092 (service name inside compose network)
  - ROW_LIMIT=4000 (each producer sends 4k rows by default in compose)
- Per-service environment overrides:
  - producer-a: PRODUCER=producer_A.py
  - producer-b: PRODUCER=producer_B.py
  - producer-c: PRODUCER=producer_C.py

 Each script:
 - Filters data/sensor_data.csv to its device ID
 - Streams rows in ascending timestamp order
 - Sends each row as JSON to topic sensor_data, then sleeps ~0.2s

## Consumer Service
The consumer connects to Kafka and ClickHouse, batches messages, and inserts rows.

- Image: built from `consumer/Dockerfile` (`python:3.9-slim`)
- Dependencies: `kafka-python`, `clickhouse-driver`
- Environment variables:
  - `KAFKA_BROKER`: Kafka address (default `localhost:9092`; in compose `kafka:9092`)
  - `KAFKA_TOPIC`: Kafka topic name (default `sensor_data`)
  - `BATCH_SIZE`: Max rows per insert (default `100`)
  - `FLUSH_INTERVAL_SEC`: Max seconds before a flush (default `2.0`)
  - `CLICKHOUSE_HOST`: ClickHouse host (default `localhost`; in compose `clickhouse-server`)
  - `CLICKHOUSE_USER`: ClickHouse username (default `default`; in compose `sensor`)
  - `CLICKHOUSE_PASSWORD`: ClickHouse password (default empty; in compose `sensorpass`)

 Schema management:
 - Centralized via init scripts mounted to `/docker-entrypoint-initdb.d`.
 - Table engine: `MergeTree`; order key: `(device_id, ts)`.

Insert mapping details:
- `ts` is converted using `datetime.utcfromtimestamp(float(ts))` → `DateTime64(3)`
- `light`, `motion` are coerced to `int(bool(...))` → `UInt8`

Manual connectivity test from the consumer container:
```
docker exec consumer python -c "from clickhouse_driver import Client; import os; \
print(os.getenv('CLICKHOUSE_USER'), os.getenv('CLICKHOUSE_PASSWORD')); \
print(Client(host='clickhouse-server', port=9000, user=os.getenv('CLICKHOUSE_USER'), \
password=os.getenv('CLICKHOUSE_PASSWORD')).execute('SELECT 1'))"
```

## Running the Image Manually
Show help:
`
docker run --rm sensor-producer --help
`

Run defaults (A, 10 rows from image env):
`
docker run --rm sensor-producer
`

Override script and rows via env vars:
`
docker run --rm -e PRODUCER=producer_B.py -e ROW_LIMIT=25 sensor-producer
`

Run by args (script and rows):
`
docker run --rm sensor-producer run producer_C.py 5
`

Mount local data (Windows PowerShell example):
`
docker run --rm -v "%cd%\data":/app/data -e PRODUCER=producer_A.py -e ROW_LIMIT=all sensor-producer
`
For macOS/Linux shells, use $(pwd) instead of %cd%.

## Topic and Message Verification
Open a shell in the broker container:
`
docker exec -it kafka bash
`

List topics:
`
kafka-topics --bootstrap-server localhost:9092 --list
`

Consume from sensor_data:
`
kafka-console-consumer --bootstrap-server localhost:9092 --topic sensor_data --from-beginning --max-messages 10
`

Expected event example:
`
{"data": {"co": 0.0031, "humidity": 76.0, "light": false, "lpg": 0.0052, "motion": false, "smoke": 0.0136, "temp": 19.7}, "device_id": "00:0f:00:70:91:0a", "ts": 1594512106.869076}
`

## Configuration Reference
- PRODUCER: script file under /app/producers (default: producer_A.py)
- ROW_LIMIT: integer or all; if invalid, script falls back to 5 rows
- KAFKA_BROKER: broker address for producers; set to kafka:9092 in compose, defaults to localhost:9092 if unset
 - Consumer-specific:
   - CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD
   - KAFKA_TOPIC, BATCH_SIZE, FLUSH_INTERVAL_SEC

## Troubleshooting
- NoBrokersAvailable in producers:
  - Ensure broker is healthy (ps), and KAFKA_BROKER resolves to kafka:9092 inside the compose network
- Topic not found:
  - Auto-create is enabled; if disabled, create sensor_data before producing
- Advertised listener mismatch:
  - Use KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
- Orphan container name conflicts:
  - Remove prior container: docker rm -f kafka
- Data path errors:
  - Ensure data/sensor_data.csv exists for the image or bind mount

### Graceful Fallback When Kafka Is Unavailable
If Kafka is not reachable, producers switch to a dry-run mode:
- A warning is printed: Kafka unavailable (NoBrokersAvailable). Running in dry-run; events printed only.
- Each event is printed with [DRY-RUN] { ... } instead of being sent to Kafka.
- This allows docker run sensor-producer to succeed even without the broker.

Example:
`
docker run --rm -e PRODUCER=producer_B.py -e ROW_LIMIT=3 sensor-producer
`

Additional consumer tips:
- Consumer shows "ClickHouse not reachable":
  - Confirm `clickhouse-server` is `healthy` via `docker compose ps`
  - Verify credentials: `sensor/sensorpass` and host `clickhouse-server`
  - Test client from inside consumer (see manual connectivity test)
  - Table creation runs on first ClickHouse start via init scripts; manual creation is optional for debugging.

Init scripts behavior:
- Scripts in `/docker-entrypoint-initdb.d` run on first start when the data directory is empty.
- To rerun, recreate ClickHouse with a fresh data directory: `docker compose up -d --force-recreate clickhouse-server`.

- Producers stuck in dry-run mode (`[DRY-RUN]` logs):
  - Ensure Kafka is reachable at `kafka:9092` inside the compose network
  - Restart producers: `docker compose restart producer-a producer-b producer-c`

- Consumer logs appear empty:
  - Logs can be buffered; to get unbuffered output, set the consumer command to `python -u consumer.py` in compose, then recreate the container.

## Verification
- Count rows in ClickHouse:
```
docker exec clickhouse-server clickhouse-client -q "SELECT count(*) FROM default.sensor_data" -u sensor --password sensorpass
```
- Sample recent rows:
```
docker exec clickhouse-server clickhouse-client -q "SELECT * FROM default.sensor_data ORDER BY ts DESC LIMIT 10" -u sensor --password sensorpass
```

## Lifecycle
- View logs:
```
docker compose logs -f
```
- Stop stack:
```
docker compose down
```

## Change Log (summarized from git)
- Initialize repo and project assets (compose, entrypoint, producers, data, README)
- Add Kafka producers and publish events to sensor_data via kafka-python
- Build Docker Compose configuration for Kafka (KRaft) and producers; update 
equirements.txt
- Merge module 2 into main; docs consolidated here

## Notes
- The producers convert light and motion to booleans, and 	s to float for consistent JSON output
- producer.flush() is called at the end to ensure messages are delivered
 - The consumer converts `light` and `motion` to `UInt8` (0/1) and parses `ts` to `DateTime64(3)` before insertion
