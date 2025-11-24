#!/bin/sh
# This script ensures the TigerBeetle data file is formatted before starting the server.
set -e

# The path to the data file inside the container
DATA_FILE="/data/0_0.tigerbeetle"

# Check if the data file has been formatted.
# The 'start' command will fail if the file is not formatted.
if [ ! -f "$DATA_FILE" ]; then
  echo "TigerBeetle data file not found at $DATA_FILE. Formatting..."
  # Format the data file for a single-node cluster.
  /tigerbeetle format --cluster=0 --replica=0 --replica-count=1 "$DATA_FILE"
else
  echo "TigerBeetle data file found. Skipping format."
fi

# Execute the command passed to the container (e.g., the 'start' command from docker-compose).
exec "$@"
