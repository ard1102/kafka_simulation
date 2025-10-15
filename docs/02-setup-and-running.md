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

## Observability: Logs with Loki + Promtail
- The stack includes `loki` (log storage) and `promtail` (log collector).
- Grafana provisions a `Loki` datasource automatically from `grafana/provisioning/datasources/loki.yml`.
- View logs in Grafana:
  - Open: `http://localhost:3000`
  - Go to `Explore` and choose the `Loki` datasource.
  - Example queries:
    - `{service="consumer"}`
    - `{service="producer-a"}`
    - `{service="kafka"}`
    - `{stream="stderr"}`
  - Available labels: `service`, `container`, `project`, `stream`.

### Optional: Start logs only when needed (Compose profiles)
You can gate observability behind a profile so it runs only on demand. Add this to the corresponding services in `docker-compose.yml`:

```yaml
services:
  loki:
    profiles: ["observability"]
    # ...
  promtail:
    profiles: ["observability"]
    # ...
```

- Start with logs: `docker compose --profile observability up -d`
- Start without logs: `docker compose up -d`

### Verify Loki ingestion
- See labels: `curl http://localhost:3100/loki/api/v1/labels`
- Sample query: `curl "http://localhost:3100/loki/api/v1/query?query=%7Bservice%3D%22consumer%22%7D&limit=5"`

### Troubleshooting
- Promtail config parsing errors:
  - Ensure the pipeline stage uses `- docker:` and is nested under the `docker` job’s `pipeline_stages`.
  - Use `$1` (not `${1}`) in relabel path: `/var/lib/docker/containers/$1/$1-json.log`.
- No logs in Grafana Explore:
  - Check containers: `docker compose ps`
  - Check Promtail: `docker compose logs -f promtail`
  - Check Loki: `docker compose logs -f loki`

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
 - Logs datasource `Loki` is auto-provisioned; use `Explore` for log viewing.

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