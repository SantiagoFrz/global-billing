#!/bin/sh
set -eu

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
root="${BACKUP_ROOT:-/backups}"
daily="$root/daily/$stamp"
mkdir -p "$daily"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  --host="${POSTGRES_HOST:-postgres}" --port="${POSTGRES_PORT:-5432}" \
  --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
  --format=custom --compress=9 --file="$daily/postgres.dump"

tar -C /data -czf "$daily/media.tar.gz" media
printf '{"created_at":"%s","database":"%s","version":"%s"}\n' \
  "$(date -u +%FT%TZ)" "$POSTGRES_DB" "${APP_VERSION:-unknown}" > "$daily/manifest.json"

# Retain 7 daily snapshots. Weekly/monthly copies are materialized on Sundays/day 1.
find "$root/daily" -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf -- {} +
if [ "$(date -u +%u)" = "7" ]; then
  mkdir -p "$root/weekly" && cp -a "$daily" "$root/weekly/$stamp"
fi
if [ "$(date -u +%d)" = "01" ]; then
  mkdir -p "$root/monthly" && cp -a "$daily" "$root/monthly/$stamp"
fi
find "$root/weekly" -mindepth 1 -maxdepth 1 -type d -mtime +28 -exec rm -rf -- {} + 2>/dev/null || true
find "$root/monthly" -mindepth 1 -maxdepth 1 -type d -mtime +186 -exec rm -rf -- {} + 2>/dev/null || true

if [ -n "${BACKUP_S3_URI:-}" ] && command -v aws >/dev/null 2>&1; then
  aws s3 sync "$root" "$BACKUP_S3_URI" --only-show-errors
fi
echo "Backup completed: $daily"
