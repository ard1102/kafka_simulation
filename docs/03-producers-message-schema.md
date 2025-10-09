# Producers and Message Schema

Three producers read `data/sensor_data.csv`, filter by specific device IDs, and publish JSON to the `sensor_data` topic.

## Producers
- Producer A: device `00:0f:00:70:91:0a`
- Producer B: device `1c:bf:ce:15:ec:4d`
- Producer C: device `b8:27:eb:bf:9d:51`

Each producer:
- Loads CSV rows
- Filters by its device
- Serializes to JSON
- Sends to `sensor_data`

## Configuration
- `KAFKA_BROKER` (e.g., `kafka-broker:9092`)
- `ROW_LIMIT` to cap rows (or `--rows` CLI arg)
- `PRODUCER` identifier for logs (optional)

## Dry-Run Resilience
If Kafka is unavailable or times out, producers can fall back to a dry-run mode that logs intended sends without publishing.

## JSON Message Format
Example payload:
```
{
  "device_id": "00:0f:00:70:91:0a",
  "ts": "2016-02-11 17:47:27",
  "data": {
    "co": 0.0012,
    "humidity": 43.2,
    "light": 120.0,
    "lpg": 0.0034,
    "motion": 0,
    "smoke": 0.0011,
    "temp": 22.5
  }
}
```

## Topic
- Name: `sensor_data`
- Key: none (messages are unkeyed unless explicitly set)
- Ordering: best-effort across partitions (single partition for simplicity in this stack)

## Running Manually
Run a producer container and override variables as needed:
- `docker run --rm --network sensor-net -e KAFKA_BROKER=kafka-broker:9092 -e ROW_LIMIT=100 <producer-image>`