# Sensor Producer

Containerized sensor data streamer that reads from `data/sensor_data.csv` and outputs JSON rows using selectable producer scripts.

## Features
- Three producer scripts: `producer_A.py`, `producer_B.py`, `producer_C.py`
- Configurable row count via `ROW_LIMIT` (number or `all`)
- Built-in `--help` showing scripts, env vars, and examples
- Minimal Python base image, only `pandas` required

## Project Structure
```
.
├── data/
│   └── sensor_data.csv
├── producers/
│   ├── dockerfile
│   ├── producer_A.py
│   ├── producer_B.py
│   └── producer_C.py
├── requirements.txt
└── README.md
```

## Build
From repository root:
```
docker build -f .\producers\dockerfile -t sensor-producer .
```

## Quick Start
Run default (producer A, 10 rows):
```
docker run --rm sensor-producer
```

Show help/usage:
```
docker run --rm sensor-producer --help
```

## Configuration
- `PRODUCER`: filename in `/app/producers` (default: `producer_A.py`)
- `ROW_LIMIT`: integer number of rows or `all` (default: `10`)

Examples:
```
# Use producer B for 10 rows
docker run --rm -e PRODUCER=producer_B.py -e ROW_LIMIT=10 sensor-producer

# Use producer C for all rows
docker run --rm -e PRODUCER=producer_C.py -e ROW_LIMIT=all sensor-producer

# Select by args (script and rows)
docker run --rm sensor-producer run producer_C.py 5
```

## Data Mount (optional)
To use your local data dynamically instead of the baked image data:
```
docker run --rm -v "%cd%\data":/app/data -e PRODUCER=producer_A.py -e ROW_LIMIT=all sensor-producer
```

## Notes
- The scripts expect `./data/sensor_data.csv` relative to `/app`.
- `producer_*` scripts filter by specific device IDs and stream JSON lines with a short delay.
- For non-Windows shells, replace `%cd%` with `$(pwd)` in mount examples.