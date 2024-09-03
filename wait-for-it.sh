#!/usr/bin/env bash

# Description:
# This script waits for a specific host and port to become available before executing
# a given command. It is useful in Docker environments where one service depends on
# another service being fully ready (e.g., a web app waiting for a database to start).

# Usage:
# ./wait-for-it.sh <HOST> <PORT> -- <COMMAND>
# Example:
# ./wait-for-it.sh localhost 27017 -- streamlit run app.py

# Assign the first two arguments to HOST and PORT
HOST=$1
PORT=$2

# Loop until the specified HOST and PORT are available
echo "Waiting for '$HOST:$PORT' to be available..."
while ! bash -c "echo > /dev/tcp/$HOST/$PORT" 2>/dev/null; do
  # Sleep for 1 second before checking again
  sleep 1
done

# Once the HOST and PORT are available, print a success message
echo "$HOST:$PORT is available, starting the application."

# Execute the command provided as additional arguments to the script
exec "${@:3}"
