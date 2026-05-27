#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  echo "ERROR: .env file is missing. Create it from .env.example before running backups."
  exit 1
fi

source .env
BACKUP_DIR="$(pwd)/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%F_%H%M%S")

if docker ps --format '{{.Names}}' | grep -q webvory_postgres; then
  docker exec -t webvory_postgres pg_dumpall -U "$POSTGRES_USER" > "$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"
  echo "PostgreSQL backup saved to $BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"
else
  echo "PostgreSQL container not found. Skipping DB backup."
fi

if docker ps --format '{{.Names}}' | grep -q webvory_redis; then
  docker exec -t webvory_redis redis-cli save
  docker cp webvory_redis:/data/dump.rdb "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb" 2>/dev/null || true
  echo "Redis backup saved to $BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"
else
  echo "Redis container not found. Skipping Redis backup."
fi

echo "Backup completed."
