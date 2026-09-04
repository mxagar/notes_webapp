"""Integration tests for authentication and note workflows."""

# Pylint does not understand pytest's name-based fixture injection.
# pylint: disable=redefined-outer-name

from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.contrib.staticfiles import finders
from django.test import Client
from django.urls import reverse
import pytest

from notes.models import Note


def test_project_static_assets_are_discoverable() -> None:
    assert finders.find("css/app.css") is not None
    assert finders.find("js/autosave.js") is not None


@pytest.mark.django_db
def test_home_redirects_anonymous_user_to_login(client: Client) -> None:
    response = client.get(reverse("home"))

    assert response.status_code == 302
    assert response.headers["Location"] == reverse("login")


@pytest.mark.django_db
def test_home_redirects_authenticated_user_to_notes(
    authenticated_client: Client,
) -> None:
    response = authenticated_client.get(reverse("home"))

    assert response.status_code == 302
    assert response.headers["Location"] == reverse("notes:list")


@pytest.mark.django_db
def test_registration_creates_and_logs_in_user(client: Client) -> None:
    response = client.post(
        reverse("register"),
        {
            "username": "new-user",
            "password1": "a-very-secure-password-123",
            "password2": "a-very-secure-password-123",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == reverse("notes:list")
    assert User.objects.filter(username="new-user").exists()
    assert client.session.get("_auth_user_id") is not None


@pytest.mark.django_db
def test_notes_require_authentication(client: Client) -> None:
    response = client.get(reverse("notes:list"))

    assert response.status_code == 302
    assert response.headers["Location"].startswith(reverse("login"))


@pytest.mark.django_db
def test_list_only_contains_current_users_notes(
    authenticated_client: Client, user: User, other_user: User
) -> None:
    own_note = Note.objects.create(owner=user, title="Mine")
    Note.objects.create(owner=other_user, title="Not mine")

    response = authenticated_client.get(reverse("notes:list"))

    assert response.status_code == 200
    assert list(response.context["notes"]) == [own_note]
    assert b"Mine" in response.content
    assert b"Not mine" not in response.content


@pytest.mark.django_db
def test_create_is_post_only_and_opens_editor(
    authenticated_client: Client, user: User
) -> None:
    get_response = authenticated_client.get(reverse("notes:create"))
    response = authenticated_client.post(reverse("notes:create"))

    note = Note.objects.get(owner=user)
    assert get_response.status_code == 405
    assert note.title == "Untitled note"
    assert response.status_code == 302
    assert response.headers["Location"] == reverse("notes:edit", args=[note.pk])


@pytest.mark.django_db
def test_explicit_save_updates_note(authenticated_client: Client, user: User) -> None:
    note = Note.objects.create(owner=user, title="Old")

    response = authenticated_client.post(
        reverse("notes:edit", args=[note.pk]),
        {"title": "New title", "body": "New body"},
    )

    note.refresh_from_db()
    assert response.status_code == 302
    assert note.title == "New title"
    assert note.body == "New body"


@pytest.mark.django_db
def test_autosave_updates_note(authenticated_client: Client, user: User) -> None:
    note = Note.objects.create(owner=user, title="Draft")

    response = authenticated_client.post(
        reverse("notes:autosave", args=[note.pk]),
        {
            "title": "Autosaved",
            "body": "Background update",
            "updated_at": note.updated_at.isoformat(),
        },
    )

    note.refresh_from_db()
    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    assert note.title == "Autosaved"


@pytest.mark.django_db
def test_autosave_rejects_stale_update(
    authenticated_client: Client, user: User
) -> None:
    note = Note.objects.create(owner=user, title="Current")

    response = authenticated_client.post(
        reverse("notes:autosave", args=[note.pk]),
        {"title": "Stale", "body": "", "updated_at": "2000-01-01T00:00:00+00:00"},
    )

    note.refresh_from_db()
    assert response.status_code == 409
    assert response.json()["status"] == "conflict"
    assert note.title == "Current"


@pytest.mark.django_db
def test_autosave_validates_title(authenticated_client: Client, user: User) -> None:
    note = Note.objects.create(owner=user, title="Current")

    response = authenticated_client.post(
        reverse("notes:autosave", args=[note.pk]),
        {"title": "", "body": "", "updated_at": note.updated_at.isoformat()},
    )

    assert response.status_code == 400
    assert "title" in response.json()["errors"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "route_name", ["notes:edit", "notes:autosave", "notes:export", "notes:delete"]
)
def test_other_users_note_is_not_accessible(
    authenticated_client: Client, other_user: User, route_name: str
) -> None:
    note = Note.objects.create(owner=other_user, title="Private")
    url = reverse(route_name, args=[note.pk])

    response = (
        authenticated_client.post(url, {})
        if route_name == "notes:autosave"
        else authenticated_client.get(url)
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_export_downloads_plain_text(authenticated_client: Client, user: User) -> None:
    note = Note.objects.create(owner=user, title="Launch plan", body="Ship it.")

    response = authenticated_client.get(reverse("notes:export", args=[note.pk]))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert response["Content-Disposition"] == 'attachment; filename="launch-plan.txt"'
    assert b"Launch plan" in response.content
    assert b"Ship it." in response.content


@pytest.mark.django_db
def test_delete_requires_post_then_removes_note(
    authenticated_client: Client, user: User
) -> None:
    note = Note.objects.create(owner=user, title="Disposable")
    url = reverse("notes:delete", args=[note.pk])

    confirmation = authenticated_client.get(url)
    assert confirmation.status_code == 200
    assert Note.objects.filter(pk=note.pk).exists()

    response = authenticated_client.post(url)
    assert response.status_code == 302
    assert response.headers["Location"] == reverse("notes:list")
    assert not Note.objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
def test_health_checks_database(client: Client) -> None:
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
