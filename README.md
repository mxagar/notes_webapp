# Notes Webapp

A small Django application for testing deployment methods and
platforms. The feature set is intentionally compact: users register, log in,
and manage private plain-text notes. The repository includes the operational
pieces expected by a real service—PostgreSQL, Gunicorn, migrations, health
checks, containers, CI, and reproducible quality tooling.

I created this application with GPT 5.6 Sol-High; the initial prompt is [`prompt.md`](./prompt.md).

The complete product contract is in [SPEC.md](SPEC.md).

## Features

- Django authentication with registration, login, and POST-only logout
- Per-user notes with strict ownership checks
- Create, edit, autosave-on-blur, explicit save, export, and delete
- Stale-write detection for background autosaves
- Responsive interface with a no-JavaScript Save fallback
- PostgreSQL for local containers, CI, and deployments
- Database-aware `/health/` endpoint
- Docker Compose development stack and production-shaped Docker image
- Optional Nginx reverse proxy through a Compose profile
- GitHub Actions checks on pull requests and pushes to `main`

![Login](./assets/login.png)

![Notes List](./assets/notes_list.png)

![Note](./assets/note.png)


## Architecture

```mermaid
flowchart LR
    B[Browser] -->|direct :8000| G[Gunicorn]
    B -. optional :8080 .-> X[Nginx reverse proxy]
    X --> G
    G --> D[Django]
    D --> A[Authentication]
    D --> N[Notes app]
    D --> W[WhiteNoise static assets]
    A --> P[(PostgreSQL)]
    N --> P
    H[Health probe] --> D
```

The Django source uses a `src/` layout:

```text
.
├── src/
│   ├── manage.py
│   ├── config/             # settings, root URLs, WSGI/ASGI entry points
│   ├── notes/              # model, forms, views, URLs, and migration
│   ├── templates/          # shared, account, and note templates
│   ├── static/             # CSS and autosave JavaScript
│   └── entrypoint.sh       # migrate, collect assets, start Gunicorn
├── .github/workflows/ci.yml
├── .env.example            # documented local configuration template
├── deploy/nginx/default.conf
├── tests/
│   ├── conftest.py         # ephemeral PostgreSQL and shared pytest fixtures
│   ├── test_database.py    # PostgreSQL contract
│   ├── test_forms.py       # form unit tests
│   ├── test_models.py      # model unit tests
│   └── test_views.py       # authentication and note workflows
├── Dockerfile
├── docker-compose.yaml
├── noxfile.py
├── pyproject.toml
├── uv.lock
└── SPEC.md
```

Browser requests enter through `config.urls`. Authentication is provided by
Django, while `notes.views` owns the note workflow and always scopes database
queries to `request.user`. `NoteForm` validates explicit and background saves.
The single initial migration creates the user-to-note relationship and its
list-ordering index.

## Quick start with Docker

Requirements: Docker with the Compose plugin.

This checkout includes a git-ignored `.env` containing generated local secrets
and all variables needed by Compose. A fresh clone will not include that file;
create it from the committed template and replace both secret placeholders:

```bash
cp .env.example .env
chmod 600 .env
```

Never commit `.env` or reuse its local credentials in a public deployment.

### Direct mode

```bash
docker compose up --build
```

Open <http://localhost:8000>, register an account, and create a note. The web
container waits for PostgreSQL, applies migrations, collects static files, and
starts Gunicorn automatically.

### Optional Nginx proxy

Enable the `proxy` profile to add Nginx in front of Django:

```bash
docker compose --profile proxy up --build
```

Open <http://localhost:8080> for proxied traffic. The direct Gunicorn endpoint
remains available at <http://localhost:8000>, which makes it easy to compare
platform behavior with and without a reverse proxy. Change `NGINX_PORT` or
`WEB_PORT` in `.env` if either host port is already occupied.

The proxy forwards `Host`, `X-Real-IP`, `X-Forwarded-For`, and
`X-Forwarded-Proto`; `/nginx-health` checks Nginx itself while `/health/`
continues through Django to PostgreSQL.

Stop the services without deleting note data:

```bash
docker compose down
```

Delete the local PostgreSQL volume as well:

```bash
docker compose down --volumes
```

The generated `.env` credentials are local-only. Replace them before exposing
this stack and never commit `.env`.

## Native development

Requirements:

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL available locally

Create the Python environment from the checked-in lockfile:

```bash
uv sync --locked --group dev
```

Start only PostgreSQL, load the local variables into the current shell, then
prepare and run Django:

```bash
docker compose up -d db
set -a
source .env
set +a
```

The `.env` `DATABASE_URL` uses the database port published by Compose. If that
port is occupied, change both `POSTGRES_PORT` and the port in `DATABASE_URL`.
This checkout's generated `.env` uses host port `55432` because `5432` was
already occupied during verification.

```bash
uv run python src/manage.py migrate
uv run python src/manage.py runserver
```

The development server is then available at <http://127.0.0.1:8000>.

Apply a model change by creating and running a migration:

```bash
uv run python src/manage.py makemigrations
uv run python src/manage.py migrate
```

Create an admin account if you want to inspect `/admin/`:

```bash
uv run python src/manage.py createsuperuser
```

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql://notes:notes@localhost:5432/notes` | PostgreSQL URL |
| `DJANGO_DEBUG` | `true` | development diagnostics; set `false` publicly |
| `DJANGO_SECRET_KEY` | insecure development value | required when debug is false |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | comma-separated hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | comma-separated public HTTPS origins |
| `DJANGO_SECURE_SSL_REDIRECT` | `false` | redirect HTTP to HTTPS |
| `DJANGO_SECURE_HSTS_SECONDS` | `0` | HSTS duration; enable only after HTTPS works |
| `PORT` | `8000` | Gunicorn port |
| `GUNICORN_WORKERS` | `2` | Gunicorn worker processes |
| `WEB_PORT` | `8000` | direct Gunicorn host port in Compose |
| `NGINX_PORT` | `8080` | optional Nginx host port |
| `POSTGRES_DB` | `notes` | Compose database name |
| `POSTGRES_USER` | `notes` | Compose database user |
| `POSTGRES_PASSWORD` | none | required Compose database secret |
| `POSTGRES_PORT` | `5432` | PostgreSQL host port for native tools |

Example public configuration:

```dotenv
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=a-long-random-value-from-your-secret-manager
DJANGO_ALLOWED_HOSTS=notes.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://notes.example.com
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=true
DJANGO_SECURE_HSTS_PRELOAD=true
DATABASE_URL=postgresql://user:password@database-host:5432/notes
PORT=8000
```

Terminate TLS at the platform or reverse proxy and forward
`X-Forwarded-Proto: https`; Django is configured to trust that header when
determining whether a request is secure.

Enable HSTS only after HTTPS is working for the domain and all selected
subdomains; browsers cache this policy.

## Tests and quality checks

All tests live in the root-level `tests/` directory. Production code under
`src/` contains no test modules.

Docker must be running, but the application Compose stack does not need to be
started. The session-scoped fixture in `tests/conftest.py` uses Testcontainers
to launch PostgreSQL 16 on a random host port. Pytest-django then creates the
test database, applies migrations, isolates each database test, and removes the
database container when pytest exits. No persistent volume is created and the
suite never falls back to SQLite.

`tests/test_database.py` explicitly checks the database vendor and major
version, preventing accidental execution against a different database engine.

Run the same complete suite as CI:

```bash
uv run nox
```

The default nox sessions run:

```text
format  -> black --check
lint    -> pylint with pylint-django
types   -> mypy with django-stubs
tests   -> pytest with pytest-django
```

Run one session or a targeted test while developing:

```bash
uv run nox -s tests
uv run pytest
uv run pytest tests/test_views.py -k autosave
```

Override the test image when evaluating another PostgreSQL release:

```bash
TEST_POSTGRES_IMAGE=postgres:17-alpine uv run pytest
```

The first test run may download the PostgreSQL and Testcontainers cleanup
images. Later runs reuse Docker's local image cache.

Check that models and migrations agree:

```bash
uv run python src/manage.py makemigrations --check --dry-run
```

## CI/CD

`.github/workflows/ci.yml` runs on every pull request targeting `main` and every
push to `main`. It installs the locked Python 3.12 environment with uv and
executes all nox sessions. Pytest provisions ephemeral PostgreSQL 16 through
Testcontainers using the Docker service already available on GitHub-hosted
runners. The workflow is a CI and deployment-readiness baseline; it
deliberately does not publish to a specific host so this repository can be
reused across deployment experiments.

## Deployment notes

The image starts through `src/entrypoint.sh`, which applies migrations and
collects static assets before launching Gunicorn. This is convenient for a
single demonstration instance. For multiple replicas, run migrations once as
a release/pre-deploy job to avoid every replica doing the same startup work.

Nginx is intentionally optional and does not terminate TLS in this template.
For public use, either terminate TLS at the hosting platform/load balancer or
extend `deploy/nginx/default.conf` with mounted certificates. The included
configuration is mounted read-only by Compose.

Use a managed secret store, a durable PostgreSQL service, HTTPS, backups, and a
platform-specific readiness check against `/health/`. Do not use Django's
development server or the Compose credentials for a public deployment.
