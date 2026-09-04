#!/bin/sh
set -eu

/app/.venv/bin/python src/manage.py migrate --noinput
/app/.venv/bin/python src/manage.py collectstatic --noinput

exec /app/.venv/bin/gunicorn config.wsgi:application \
  --chdir src \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --access-logfile - \
  --error-logfile -
