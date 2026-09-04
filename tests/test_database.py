"""Guards for the test database contract."""

from django.db import connection
import pytest


@pytest.mark.django_db
def test_suite_uses_ephemeral_postgresql_16() -> None:
    assert connection.vendor == "postgresql"

    with connection.cursor() as cursor:
        cursor.execute("SHOW server_version")
        version = cursor.fetchone()

    assert version is not None
    assert str(version[0]).startswith("16.")
