# Setup and Running

Follow these steps to bring up the full pipeline with Docker Compose and verify data flow end-to-end.

## Prerequisites
- Docker Desktop (latest)
- Docker Compose v2 (bundled with Docker Desktop)

## Build Images
- Build the producer image so the local Compose file can use it:
  - `docker compose build`
- If producers have their own `Dockerfile`, ensure it’s in `producers/` and referenced by the Compose service.

## Environment
- Grafana credentials can be set via environment variables in Compose:
  - `GF_SECURITY_ADMIN_USER=admin`
  - `GF_SECURITY_ADMIN_PASSWORD=admin`
- Kafka broker address is set in services via environment (e.g., `KAFKA_BROKER=kafka-broker:9092`).

## Start the Stack
- From the project root (where `docker-compose.yml` lives):
  - `docker compose up -d`
- This starts Kafka, ClickHouse, three producers, the consumer, and Grafana on a shared network.

## Check Status
- See container status: `docker compose ps`
- Tail consumer logs for ingestion progress: `docker compose logs -f consumer`
- Restart the producers if Kafka was briefly unavailable: `docker compose restart producer-a producer-b producer-c`

## Verify Kafka
- List topics: `docker compose exec kafka-broker kafka-topics.sh --list --bootstrap-server localhost:9092`
- Consume test messages: `docker compose exec kafka-broker kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic sensor_data --from-beginning --max-messages 10`

## Verify ClickHouse
- Port `8123` (HTTP) is exposed. Example queries:
  - Count rows: `SELECT count() FROM default.sensor_data;`
  - Sample rows: `SELECT * FROM default.sensor_data LIMIT 10;`
- Use your browser or an HTTP client: `http://localhost:8123`

## Grafana
- Access: `http://localhost:3000`
- Datasource is auto-provisioned (`grafana/provisioning/datasources/clickhouse.yml`).
- Dashboards are auto-loaded from `grafana/dashboards/`.

## Troubleshooting
- `NoBrokersAvailable`: Restart producers after Kafka is healthy.
- Topic missing: Ensure `auto.create.topics.enable` is on, or create manually.
- Advertised listeners mismatch: Use the container hostname (`kafka-broker`) inside the network.
- Orphan containers: `docker compose down -v` then `docker compose up -d`.
- ClickHouse connectivity: Check `CLICKHOUSE_HOST`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD` env.
- Buffered logs: Consumer batches inserts; logs may show periodic flushes.

## Cleanup
- Stop: `docker compose down`
- Full cleanup including volumes: `docker compose down -v`