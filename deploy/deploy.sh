#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: .env file is missing. Copy .env.example to .env and update secrets before deploying."
  exit 1
fi

echo "Pulling latest images and rebuilding the stack..."
export COMPOSE_HTTP_TIMEOUT=200
/usr/bin/docker compose pull || true
/usr/bin/docker compose up -d --build --remove-orphans

echo "Waiting for containers to stabilize..."
sleep 8
/usr/bin/docker compose ps
/usr/bin/docker compose logs --tail=20 web nginx postgres redis
