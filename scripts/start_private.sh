#!/usr/bin/env bash
# Run on the LinuxONE HOST from the existing release. No new container or port mapping.
set -euo pipefail
cd "$(dirname "$0")/.."
host_root="$PWD"
container_root="/home/ibm-user/shared/GreenPulseAI/$(basename "$host_root")"
mkdir -p "$host_root/run"
chmod 700 "$host_root/run"
if [ -e "$host_root/run/greenpulse.sock" ]; then
  echo "Existing socket found. Check the running app; do not start a duplicate." >&2
  exit 1
fi
sudo -n docker exec -d -w "$container_root" \
  -e GREENPULSE_MODEL_DIR="$container_root/artifacts/model-svm" \
  notebook .venv/bin/python -m uvicorn app.main:app \
  --uds "$container_root/run/greenpulse.sock" --no-access-log
for attempt in {1..30}; do
  if [ -S "$host_root/run/greenpulse.sock" ]; then
    exec python3 scripts/private_proxy.py --socket "$host_root/run/greenpulse.sock" --port 8003
  fi
  sleep 1
done
echo "API socket did not appear. Inspect the container before retrying." >&2
exit 1
