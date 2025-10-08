import pandas as pd
import json
import time
import argparse
import os
import sys
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable, KafkaTimeoutError

device = 'b8:27:eb:bf:9d:51'

parser = argparse.ArgumentParser(description="Sensor producer C")

# Accepts either an int or the string 'all'
parser.add_argument(
    "--rows",
    default=os.getenv("ROW_LIMIT", "5"),
    help="Number of rows to produce (int) or 'all'",
)

args = parser.parse_args()

data_path = './data/sensor_data.csv'

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        max_block_ms=int(os.getenv("KAFKA_MAX_BLOCK_MS", "1000"))
    )
except (NoBrokersAvailable, Exception) as e:
    print(f"⚠️ Kafka unavailable ({type(e).__name__}). Running in dry-run; events printed only.", file=sys.stderr)
    producer = None

# Optional quick connectivity check; switch to dry-run if metadata unavailable
if producer is not None:
    try:
        parts = producer.partitions_for('sensor_data')
        if parts is None or len(parts) == 0:
            print("⚠️ Kafka metadata unavailable. Switching to dry-run.", file=sys.stderr)
            producer = None
    except KafkaTimeoutError:
        print("⚠️ Kafka metadata unavailable (timeout). Switching to dry-run.", file=sys.stderr)
        producer = None

# Check if file exists
if not os.path.exists(data_path):
    print(f"❌ Error: Data file not found at {data_path}", file=sys.stderr)
    sys.exit(1)

# Load data
df = pd.read_csv(data_path)
df = df[df['device'] == device]

df = df.sort_values(by=["device", "ts"]).reset_index(drop=True)
# Handle row limit argument
rows_arg = str(args.rows).lower().strip()
if rows_arg == "all":
    pass  # use full dataset
else:
    try:
        n = int(rows_arg)
        df = df.head(n)
    except ValueError:
        print("⚠️ Invalid row limit provided. Defaulting to 5 rows.")
        df = df.head(5)

# Safety fallback
if df.empty:
    print("⚠️ No data found for the specified device.")
    sys.exit(0)

# Template for output JSON
json_template = {
    "data": {
        "co": None,
        "humidity": None,
        "light": None,
        "lpg": None,
        "motion": None,
        "smoke": None,
        "temp": None
    },
    "device_id": None,
    "ts": None
}

# Stream rows as JSON
for _, row in df.iterrows():
    json_output = json_template.copy()
    json_output["data"] = {
        "co": row["co"],
        "humidity": row["humidity"],
        "light": bool(row["light"]),
        "lpg": row["lpg"],
        "motion": bool(row["motion"]),
        "smoke": row["smoke"],
        "temp": row["temp"]
    }
    json_output["device_id"] = row["device"]
    json_output["ts"] = float(row["ts"])

    if producer is not None:
        try:
            future = producer.send('sensor_data', value=json_output)
            future.get(timeout=float(os.getenv("KAFKA_SEND_TIMEOUT_SEC", "1.0")))
            print(f"Sent: {json.dumps(json_output)}")
        except KafkaTimeoutError:
            print("⚠️ Send timed out. Switching to dry-run.", file=sys.stderr)
            print(f"[DRY-RUN] {json.dumps(json_output)}")
            producer = None
        except Exception as e:
            print(f"⚠️ Send failed ({type(e).__name__}). Switching to dry-run.", file=sys.stderr)
            print(f"[DRY-RUN] {json.dumps(json_output)}")
            producer = None
    else:
        print(f"[DRY-RUN] {json.dumps(json_output)}")
    time.sleep(0.4)

if producer is not None:
    producer.flush()
