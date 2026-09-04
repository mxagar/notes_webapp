"""Repeatable quality and test sessions run through uv."""

import nox

nox.options.sessions = ["format", "lint", "types", "tests"]


def uv_run(session: nox.Session, *command: str) -> None:
    """Run a locked project command in the uv-managed environment."""
    session.run("uv", "run", "--locked", *command, external=True)


@nox.session(venv_backend="none")
def format(session: nox.Session) -> None:
    """Check Python formatting without changing files."""
    uv_run(session, "black", "--check", "src", "tests", "noxfile.py")


@nox.session(venv_backend="none")
def lint(session: nox.Session) -> None:
    """Run Pylint with Django awareness."""
    uv_run(
        session,
        "pylint",
        "--ignore=migrations",
        "src/config",
        "src/notes",
        "tests",
    )


@nox.session(venv_backend="none")
def types(session: nox.Session) -> None:
    """Run static type analysis."""
    uv_run(session, "mypy", "src/config", "src/notes", "src/manage.py", "tests")


@nox.session(venv_backend="none")
def tests(session: nox.Session) -> None:
    """Run tests against a disposable PostgreSQL Testcontainer."""
    uv_run(session, "pytest")
