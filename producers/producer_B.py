import pandas as pd
import json
import time
import argparse
import os
import sys

parser = argparse.ArgumentParser(description="Sensor producer A")

# Accepts either an int or the string 'all'
parser.add_argument(
    "--rows",
    default=os.getenv("ROW_LIMIT", "5"),
    help="Number of rows to produce (int) or 'all'",
)

args = parser.parse_args()
device = '1c:bf:ce:15:ec:4d'
data_path = './data/sensor_data.csv'

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

    print(json.dumps(json_output))
    time.sleep(0.2)
