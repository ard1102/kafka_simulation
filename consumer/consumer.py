import os
import json
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from clickhouse_driver import Client

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", None)


def get_clickhouse_client(database: str | None = None) -> Client:
    return Client(
        host=CLICKHOUSE_HOST,
        port=9000,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        **({"database": database} if database else {}),
    )
TOPIC = os.getenv("KAFKA_TOPIC", "sensor_data")


def wait_for_clickhouse(max_wait_seconds=120):
    start = time.time()
    while time.time() - start < max_wait_seconds:
        try:
            # Always ping the default database to avoid failures if CLICKHOUSE_DB doesn't exist yet
            client = get_clickhouse_client("default")
            client.execute("SELECT 1")
            return client
        except Exception:
            time.sleep(2)
    raise RuntimeError("ClickHouse not reachable after wait")


def create_kafka_consumer():
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="sensor-consumer",
        )
        return consumer
    except NoBrokersAvailable as e:
        raise RuntimeError(f"Kafka not reachable: {e}")


def main():
    print("Consumer is running...")
    # Use a client bound to the target database (or default if none specified)
    client = get_clickhouse_client(CLICKHOUSE_DB if CLICKHOUSE_DB else None)
    table_fqn = f"{CLICKHOUSE_DB}.sensor_data" if CLICKHOUSE_DB else "sensor_data"
    consumer = create_kafka_consumer()

    batch = []
    batch_size = int(os.getenv("BATCH_SIZE", "100"))
    last_flush = time.time()
    flush_interval = float(os.getenv("FLUSH_INTERVAL_SEC", "2.0"))

    def flush():
        nonlocal batch
        if not batch:
            return
        try:
            client.execute(
                f"""
                INSERT INTO {table_fqn} (
                    device_id, ts, co, humidity, light, lpg, motion, smoke, temp, ingest_time
                ) VALUES
                """,
                batch,
            )
            print(f"Inserted: {len(batch)} rows into {table_fqn}")
            batch = []
        except Exception as e:
            print(f"Insert error: {e}")

    for msg in consumer:
        try:
            payload = msg.value
            device_id = payload.get("device_id")
            ts = payload.get("ts")
            data = payload.get("data", {})

            ts_dt = datetime.utcfromtimestamp(float(ts))

            row = (
                device_id,
                ts_dt,
                float(data.get("co", 0.0)),
                float(data.get("humidity", 0.0)),
                int(bool(data.get("light", False))),
                float(data.get("lpg", 0.0)),
                int(bool(data.get("motion", False))),
                float(data.get("smoke", 0.0)),
                float(data.get("temp", 0.0)),
                datetime.utcnow(),
            )
            batch.append(row)

            if len(batch) >= batch_size or (time.time() - last_flush) >= flush_interval:
                flush()
                last_flush = time.time()
        except Exception as e:
            print(f"Process error: {e}")


if __name__ == "__main__":
    main()