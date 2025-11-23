#!/usr/bin/env bash
set -euo pipefail

# .env must be present (copiar .env.template y editar)
if [ ! -f .env ]; then
  echo ".env not found. Copy .env.template to .env and set variables."
  exec sleep infinity
fi

# load env
export $(grep -v '^#' .env | xargs)

echo "Starting node ${NODE_ID} on port ${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers
