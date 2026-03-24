#!/bin/sh
set -e

# Wait for database to be reachable before running migrations
MAX_RETRIES=${DB_WAIT_RETRIES:-10}
RETRY=0
until python -c "import socket; s=socket.create_connection(('${DATABASE_HOST:-localhost}', ${DATABASE_PORT:-5432}), timeout=3); s.close()" 2>/dev/null; do
  RETRY=$((RETRY + 1))
  if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
    echo "ERROR: Database not reachable after $MAX_RETRIES attempts. Exiting."
    exit 1
  fi
  echo "Waiting for database ($RETRY/$MAX_RETRIES)..."
  sleep 3
done
echo "Database is reachable."

echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete."

exec uvicorn main:app \
    --host "${BACKEND_HOST:-0.0.0.0}" \
    --port "${BACKEND_PORT:-8000}" \
    --log-level "${LOG_LEVEL:-info}"
