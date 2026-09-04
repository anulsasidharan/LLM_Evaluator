#!/bin/sh
set -e
echo "Waiting for database..."
# Simple retry loop for Postgres readiness from the app's perspective
i=0
until uv run python -c "import asyncio; from sqlalchemy import text; from app.api.deps import get_engine; from app.config import get_settings; 
async def ping():
  eng=get_engine(get_settings());
  async with eng.connect() as c: await c.execute(text('SELECT 1'))
asyncio.run(ping())" 2>/dev/null; do
  i=$((i+1))
  if [ "$i" -gt 30 ]; then
    echo "Database not ready after 30 attempts"
    exit 1
  fi
  echo "Database unavailable ($i) — sleeping"
  sleep 2
done
echo "Starting API on :8002"
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8002
