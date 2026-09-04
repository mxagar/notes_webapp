"""Forms for accounts and notes."""

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django import forms

from .models import Note


class RegistrationForm(UserCreationForm):  # pylint: disable=too-many-ancestors
    """Registration form backed by Django's password validation."""

    class Meta:
        model = User
        fields = ("username",)


class NoteForm(forms.ModelForm):
    """Editor form for a note's user-controlled fields."""

    class Meta:
        model = Note
        fields = ("title", "body")
        widgets = {
            "title": forms.TextInput(
                attrs={"autocomplete": "off", "aria-label": "Note title"}
            ),
            "body": forms.Textarea(
                attrs={"placeholder": "Start writing…", "aria-label": "Note body"}
            ),
        }
