#!/bin/sh
set -eu

snapshot="${1:-}"
if [ -z "$snapshot" ] || [ ! -f "$snapshot/postgres.dump" ]; then
  echo "Usage: $0 /backups/{daily|weekly|monthly}/TIMESTAMP" >&2
  exit 2
fi

PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
  --host="${POSTGRES_HOST:-postgres}" --port="${POSTGRES_PORT:-5432}" \
  --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
  --clean --if-exists --no-owner "$snapshot/postgres.dump"

if [ -f "$snapshot/media.tar.gz" ]; then
  tar -C /data -xzf "$snapshot/media.tar.gz"
fi
echo "Restore completed from: $snapshot"
