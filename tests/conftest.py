"""Shared pytest fixtures, including an ephemeral PostgreSQL database."""

# Pylint does not understand pytest's name-based fixture injection.
# pylint: disable=redefined-outer-name

from collections.abc import Generator
import os

import dj_database_url
from django.conf import settings
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.db import connections
from django.test import Client
import pytest
from testcontainers.community.postgres import PostgresContainer

TEST_DATABASE_NAME = "notes_test"
TEST_DATABASE_USER = "notes_test"
TEST_DATABASE_PASSWORD = "test-only-password"


@pytest.fixture(scope="session")
def ephemeral_postgres_url() -> Generator[str, None, None]:
    """Start PostgreSQL in a disposable container and return its URL."""
    image = os.getenv("TEST_POSTGRES_IMAGE", "postgres:16-alpine")
    with PostgresContainer(
        image=image,
        username=TEST_DATABASE_USER,
        password=TEST_DATABASE_PASSWORD,
        dbname=TEST_DATABASE_NAME,
    ) as postgres:
        host = postgres.get_container_host_ip()
        port = postgres.get_exposed_port(5432)
        yield (
            f"postgresql://{TEST_DATABASE_USER}:{TEST_DATABASE_PASSWORD}"
            f"@{host}:{port}/{TEST_DATABASE_NAME}"
        )


@pytest.fixture(scope="session")
def django_db_modify_db_settings(ephemeral_postgres_url: str) -> None:
    """Point pytest-django's database setup at ephemeral PostgreSQL."""
    database_settings = dj_database_url.parse(
        ephemeral_postgres_url,
        conn_max_age=0,
        conn_health_checks=False,
    )
    settings.DATABASES["default"].update(database_settings)

    connection = connections["default"]
    connection.close()
    connection.settings_dict.update(database_settings)


@pytest.fixture
def user() -> User:
    return User.objects.create_user(username="alice", password="strong-pass-123")


@pytest.fixture
def other_user() -> User:
    return User.objects.create_user(username="bob", password="strong-pass-456")


@pytest.fixture
def authenticated_client(client: Client, user: User) -> Client:
    client.force_login(user)
    return client
