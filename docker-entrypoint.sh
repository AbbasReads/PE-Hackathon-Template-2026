#!/bin/sh
set -eu

while true
do
  python -m uvicorn run:app --host 0.0.0.0 --port 8000
  status=$?
  echo "uvicorn exited with status ${status}; restarting in 1s" >&2
  sleep 1
done
