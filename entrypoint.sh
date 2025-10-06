#!/bin/sh
set -e

show_usage() {
  echo "Sensor Producer - Docker Image"
  echo
  echo "Description:"
  echo "Streams sensor data from CSV via selected producer script."
  echo
  echo "Available producer scripts:"
  found_scripts=false
  for f in /app/producers/*.py; do
    if [ -e "$f" ]; then
      echo "  - $(basename "$f")"
      found_scripts=true
    fi
  done
  if [ "$found_scripts" = false ]; then
    echo "  (none found)"
  fi
  echo
  echo "Environment variables:"
  echo "  - PRODUCER: script filename in /app/producers (default: producer_A.py)"
  echo "  - ROW_LIMIT: number of rows or 'all' (default: 10)"
  echo
  echo "Usage:"
  echo "  - Show help: docker run --rm sensor-producer --help"
  echo "  - Run default: docker run --rm sensor-producer"
  echo "  - Override script: docker run --rm -e PRODUCER=producer_B.py sensor-producer"
  echo "  - Override rows: docker run --rm -e ROW_LIMIT=all sensor-producer"
  echo "  - Run by args: docker run --rm sensor-producer run producer_C.py 5"
}

case "$1" in
  --help|-h|help)
    show_usage
    exit 0
    ;;
  run)
    shift
    if [ -n "$1" ]; then PRODUCER="$1"; shift; fi
    if [ -n "$1" ]; then ROW_LIMIT="$1"; shift; fi
    ;;
  "" )
    ;;
  * )
    # If unknown arg, show help
    show_usage
    exit 0
    ;;
esac

PRODUCER="${PRODUCER:-producer_A.py}"
ROW_LIMIT="${ROW_LIMIT:-10}"

# Verify producer exists
if [ ! -f "/app/producers/$PRODUCER" ]; then
  echo "Error: producer script '/app/producers/$PRODUCER' not found." >&2
  echo "Use --help to list available scripts." >&2
  exit 1
fi

exec python -u "/app/producers/$PRODUCER" --rows "$ROW_LIMIT"