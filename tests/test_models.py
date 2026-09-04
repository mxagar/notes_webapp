"""Unit tests for the Note model."""

from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
import pytest

from notes.models import Note


@pytest.mark.django_db
def test_note_string_representation_is_its_title(user: User) -> None:
    note = Note.objects.create(owner=user, title="Readable title")

    assert str(note) == "Readable title"


@pytest.mark.django_db
def test_notes_are_ordered_by_most_recent_update(user: User) -> None:
    older = Note.objects.create(owner=user, title="Older")
    newer = Note.objects.create(owner=user, title="Newer")

    assert list(Note.objects.all()) == [newer, older]
