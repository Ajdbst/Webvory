#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: .env file is missing. Copy .env.example to .env and update secrets before deploying."
  exit 1
fi

echo "Pulling latest images and rebuilding the stack..."
export COMPOSE_HTTP_TIMEOUT=200
DOCKER_CMD="$(command -v docker || true)"
if [[ -z "$DOCKER_CMD" ]]; then
  echo "ERROR: docker is not installed or not in PATH. Please run deploy/install-server.sh first."
  exit 1
fi
"$DOCKER_CMD" compose pull || true
"$DOCKER_CMD" compose up -d --build --remove-orphans

echo "Waiting for containers to stabilize..."
sleep 8
"$DOCKER_CMD" compose ps
"$DOCKER_CMD" compose logs --tail=20 web nginx postgres redis
