# Notes Web Application Specification

## 1. Purpose

This repository contains a deliberately small but production-shaped Django
application. Its primary purpose is to exercise development, CI, container,
and deployment workflows rather than to compete with full-featured note-taking
products.

## 2. Scope

### In scope

- Local account registration, login, and logout using Django authentication.
- A private note collection for each authenticated user.
- Creating, listing, viewing/editing, exporting, and deleting notes.
- Automatic editor saves on field blur plus an explicit Save button.
- PostgreSQL in normal, container, and CI environments.
- A small health endpoint suitable for container and platform probes.
- A Docker image, Docker Compose stack, automated checks, and usage docs.
- An optional Nginx reverse proxy configured and distributed with the Compose
  stack.

### Out of scope

- Rich-text editing, attachments, tags, folders, search, sharing, and password
  reset email delivery.
- Social login, APIs for third-party clients, background jobs, and real-time
  collaborative editing.
- Production infrastructure definitions for a particular cloud provider.

## 3. Functional requirements

### Authentication

1. `/` redirects anonymous visitors to `/accounts/login/` and authenticated
   users to `/notes/`.
2. Login uses Django's built-in authentication backend.
3. Registration asks for username and password, applies Django's configured
   password validators, signs the new user in, and redirects to `/notes/`.
4. Logout is a POST action and returns to the login page.

### Notes

1. Each note belongs to exactly one user and cannot be read or changed by
   another user.
2. A note contains a title, plain-text body, creation timestamp, and last
   updated timestamp.
3. The list is ordered by most recently updated and displays title and date.
4. Creating a note is a POST action which creates an `Untitled note` and opens
   its editor on a separate page.
5. The editor saves a title and body through either a normal Save POST or a
   background POST triggered when either field loses focus.
6. Autosave returns JSON, shows saving/saved/error state, and uses the note's
   last-updated token to reject stale writes with HTTP 409.
7. Export downloads one note as UTF-8 plain text with a safe filename.
8. Delete requires a confirmation page and a POST submission.

### Operations

1. `/health/` returns JSON and HTTP 200 when the process can query its database.
2. Configuration comes from environment variables. Secrets are never committed.
3. Static assets are served by WhiteNoise from the application image.
4. The default Compose mode exposes Gunicorn directly for simple platform
   experiments.
5. The opt-in Compose `proxy` profile adds Nginx in front of Gunicorn, forwards
   the original host, client address, and protocol headers, and provides a
   proxy-local health endpoint.

## 4. Quality and security requirements

- Python 3.12 or newer and Django 5.2 LTS-compatible code.
- PostgreSQL is the supported application database.
- All Django application code and web assets live under the repository's
  `src/` directory. Repository-level packaging, automation, and deployment
  files remain at the root.
- All state-changing browser requests use POST and CSRF protection.
- Note lookups always include the logged-in owner.
- Templates rely on Django escaping; note bodies are edited and exported as
  plain text.
- Production mode requires an explicit secret key and configured allowed hosts.
- The container runs as an unprivileged user and exposes a health check.
- Nginx configuration is mounted read-only, hides its version, limits request
  size, and only starts after the Django service is healthy.
- Pages are responsive, keyboard accessible, and usable without JavaScript
  except for background autosave (the Save button remains the fallback).

## 5. Configuration contract

| Variable | Required | Default | Meaning |
| --- | --- | --- | --- |
| `DJANGO_SECRET_KEY` | production | development-only value | Django signing key |
| `DJANGO_DEBUG` | no | `true` | enable debug mode; disable in deployments |
| `DJANGO_ALLOWED_HOSTS` | production | `localhost,127.0.0.1` | comma-separated hosts |
| `DATABASE_URL` | no | local PostgreSQL URL | PostgreSQL connection URL |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | no | empty | comma-separated HTTPS origins |
| `DJANGO_SECURE_SSL_REDIRECT` | no | `false` | redirect HTTP to HTTPS |
| `DJANGO_SECURE_HSTS_SECONDS` | no | `0` | HSTS duration for HTTPS deployments |
| `PORT` | no | `8000` | Gunicorn bind port |
| `GUNICORN_WORKERS` | no | `2` | Gunicorn worker count |
| `WEB_PORT` | no | `8000` | direct host port for the web service |
| `NGINX_PORT` | no | `8080` | host port for the optional proxy |
| `POSTGRES_DB` | no | `notes` | Compose PostgreSQL database |
| `POSTGRES_USER` | no | `notes` | Compose PostgreSQL user |
| `POSTGRES_PASSWORD` | Compose | none | Compose PostgreSQL password |

## 6. Data model

```text
User 1 ---- * Note

Note
- id: bigint primary key
- owner_id: foreign key to auth.User, cascade delete, indexed with updated_at
- title: varchar(200)
- body: text
- created_at: timestamp with timezone
- updated_at: timestamp with timezone
```

### Source layout

```text
src/
├── manage.py
├── config/       # Django project configuration and server entry points
├── notes/        # Notes domain app, migrations, and tests
├── templates/    # Project templates
└── static/       # CSS and browser-side JavaScript

deploy/
└── nginx/
    └── default.conf  # optional reverse-proxy configuration

tests/                # root-level pytest suite and PostgreSQL fixtures
```

## 7. Deployment topology

### Direct mode (default)

```text
browser :8000 -> Gunicorn/Django :8000 -> PostgreSQL :5432
```

Start with `docker compose up --build`. This mode does not create an Nginx
container.

### Proxy mode (optional)

```text
browser :8080 -> Nginx :80 -> Gunicorn/Django :8000 -> PostgreSQL :5432
```

Start with `docker compose --profile proxy up --build`. Direct port 8000 stays
available so the same stack can be used to compare direct and proxied traffic.

## 8. Routes

| Route | Methods | Access | Result |
| --- | --- | --- | --- |
| `/` | GET | public | redirect based on authentication |
| `/accounts/login/` | GET, POST | public | login form |
| `/accounts/register/` | GET, POST | public | registration form |
| `/accounts/logout/` | POST | authenticated | end session |
| `/notes/` | GET | authenticated | note list |
| `/notes/new/` | POST | authenticated | create and redirect to editor |
| `/notes/<id>/` | GET, POST | owner | edit note |
| `/notes/<id>/autosave/` | POST | owner | JSON autosave endpoint |
| `/notes/<id>/export/` | GET | owner | text download |
| `/notes/<id>/delete/` | GET, POST | owner | confirmation and deletion |
| `/health/` | GET | public | database readiness JSON |

## 9. Verification and acceptance criteria

- All tests live in the repository-root `tests/` directory; production source
  directories contain no test modules.
- `nox` runs formatting verification, Pylint, mypy, and pytest.
- Pytest starts a fresh PostgreSQL 16 Testcontainer for each test session,
  applies Django migrations, isolates individual tests through pytest-django,
  and removes the database container at session end. SQLite is not used.
- Tests cover authentication, ownership boundaries, every note operation,
  autosave success/conflict/error behavior, and the health endpoint.
- GitHub Actions runs the same nox sessions for pull requests targeting `main`
  and pushes to `main`; the pytest session creates its own ephemeral PostgreSQL.
- `docker compose up --build` starts PostgreSQL, applies migrations, collects
  static files, and runs Gunicorn without creating an Nginx container.
- `docker compose --profile proxy up --build` additionally starts Nginx with
  the repository configuration and serves the application through it.
- `.env.example` documents every Compose variable, while a git-ignored `.env`
  supplies generated local secrets for this checkout.
- The README documents setup, architecture, configuration, checks, and common
  deployment usage, including a Mermaid architecture diagram.

## 10. Implementation plan

1. Create the uv project metadata and Django project/app skeleton under `src/`.
2. Implement configuration, the Note model, migration, routes, forms, and views.
3. Build accessible templates and static assets, including progressive autosave.
4. Add root-level unit/integration tests, ephemeral PostgreSQL fixtures, and the
   nox quality sessions.
5. Add the Docker image, optional Nginx proxy, Compose stack, startup script,
   and CI workflow.
6. Document the application and verify formatting, analysis, tests, Django,
   direct Compose, and proxied Compose behavior.
