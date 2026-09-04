"""Unit tests for account and note form validation."""

import pytest

from notes.forms import NoteForm, RegistrationForm


def test_note_form_accepts_plain_text_body() -> None:
    form = NoteForm({"title": "A title", "body": "Plain text\nSecond line"})

    assert form.is_valid()
    assert form.cleaned_data["body"] == "Plain text\nSecond line"


def test_note_form_requires_a_title() -> None:
    form = NoteForm({"title": "", "body": "Body"})

    assert not form.is_valid()
    assert "title" in form.errors


@pytest.mark.django_db
def test_registration_rejects_mismatched_passwords() -> None:
    form = RegistrationForm(
        {
            "username": "new-user",
            "password1": "a-secure-password-123",
            "password2": "a-different-password-456",
        }
    )

    assert not form.is_valid()
    assert "password2" in form.errors
