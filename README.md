# Sensor Producer + Kafka Simulation (KRaft)

Containerized sensor data producers that read from data/sensor_data.csv and publish JSON events to a Kafka topic (sensor_data). The stack runs a single-node Kafka (KRaft mode) via Docker Compose and three producer services for different device IDs.

## Overview
- Three producers: producer_A.py, producer_B.py, producer_C.py (each targets a specific device ID)
- Publishes to Kafka topic sensor_data using kafka-python
- Configurable row limit via ROW_LIMIT (integer or ll)
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
 entrypoint.sh
 docker-compose.yml
 requirements.txt
 README.md
`

## Prerequisites
- Docker Desktop installed and running
- Docker Compose v2 (use docker compose; v1 commands shown as alternatives)

## Build Producer Image
From repository root:
`
docker build -t sensor-producer -f .\producers\dockerfile .
`

Notes:
- The build copies producers/, data/, and entrypoint.sh into the image
- Default envs baked into the image: PRODUCER=producer_A.py, ROW_LIMIT=10

## Run via Docker Compose
Start Kafka (KRaft) and all producers:
`
docker compose -f c:\Users\<you>\Downloads\Rough\kafka_simulation\docker-compose.yml up -d
`
Alternative (v1):
`
docker-compose -f c:\Users\<you>\Downloads\Rough\kafka_simulation\docker-compose.yml up -d
`

Follow logs for broker and producers:
`
docker compose -f c:\Users\<you>\Downloads\Rough\kafka_simulation\docker-compose.yml logs -f
`
Alternative (v1):
`
docker-compose -f c:\Users\<you>\Downloads\Rough\kafka_simulation\docker-compose.yml logs -f
`

List services and ports:
`
docker compose -f c:\Users\<you>\Downloads\Rough\kafka_simulation\docker-compose.yml ps
`

Stop stack:
`
docker compose -f c:\Users\<you>\Downloads\Rough\kafka_simulation\docker-compose.yml down
`
Alternative (v1):
`
docker-compose -f c:\Users\<you>\Downloads\Rough\kafka_simulation\docker-compose.yml down
`

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
- ROW_LIMIT: integer or ll; if invalid, script falls back to 5 rows
- KAFKA_BROKER: broker address for producers; set to kafka:9092 in compose, defaults to localhost:9092 if unset

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

## Change Log (summarized from git)
- Initialize repo and project assets (compose, entrypoint, producers, data, README)
- Add Kafka producers and publish events to sensor_data via kafka-python
- Build Docker Compose configuration for Kafka (KRaft) and producers; update equirements.txt
- Merge module 2 into main; docs consolidated here

## Notes
- The producers convert light and motion to booleans, and 	s to float for consistent JSON output
- producer.flush() is called at the end to ensure messages are delivered
