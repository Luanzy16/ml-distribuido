#!/usr/bin/env bash
set -euo pipefail

# .env debe existir
if [ ! -f /app/.env ]; then
  echo ".env not found. Copy .env.template to .env and set variables."
  exec sleep infinity
fi

# carga variables de entorno
export $(grep -v '^#' .env | xargs)

echo "Starting node ${NODE_ID} on port ${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers
