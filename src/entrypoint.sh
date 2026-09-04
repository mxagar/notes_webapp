#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS_ON_STARTUP:-true}" = "true" ]; then
  /app/.venv/bin/python src/manage.py migrate --noinput
fi

/app/.venv/bin/python src/manage.py collectstatic --noinput

exec /app/.venv/bin/gunicorn config.wsgi:application \
  --chdir src \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --access-logfile - \
  --error-logfile -
