"""HTTP views for authentication and private notes."""

from typing import Any, cast

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.db import connection
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .forms import NoteForm, RegistrationForm
from .models import Note


def home(request: HttpRequest) -> HttpResponse:
    """Send visitors to the appropriate application entry point."""
    if request.user.is_authenticated:
        return redirect("notes:list")
    return redirect("login")


def register(request: HttpRequest) -> HttpResponse:
    """Create an account and sign it in."""
    if request.user.is_authenticated:
        return redirect("notes:list")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("notes:list")
    return render(request, "registration/register.html", {"form": form})


def health(_request: HttpRequest) -> JsonResponse:
    """Confirm that Django can query its database."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ok"})


@login_required
def note_list(request: HttpRequest) -> HttpResponse:
    """Show only the signed-in user's notes."""
    owner = cast(User, request.user)
    notes = Note.objects.filter(owner=owner)
    return render(request, "notes/note_list.html", {"notes": notes})


@require_POST
@login_required
def note_create(request: HttpRequest) -> HttpResponse:
    """Create an empty note and open its editor."""
    owner = cast(User, request.user)
    note = Note.objects.create(owner=owner, title="Untitled note")
    return redirect("notes:edit", pk=note.pk)


@login_required
def note_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Display or explicitly save a note owned by the current user."""
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    form = NoteForm(request.POST or None, instance=note)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("notes:edit", pk=note.pk)
    return render(
        request,
        "notes/note_editor.html",
        {"form": form, "note": note},
    )


@require_POST
@login_required
def note_autosave(request: HttpRequest, pk: int) -> JsonResponse:
    """Save editor fields unless another request updated the note first."""
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    expected = request.POST.get("updated_at", "")
    if expected != note.updated_at.isoformat():
        return JsonResponse(
            {"status": "conflict", "message": "This note changed elsewhere."},
            status=409,
        )

    form = NoteForm(request.POST, instance=note)
    if not form.is_valid():
        errors: dict[str, Any] = form.errors.get_json_data()
        return JsonResponse({"status": "error", "errors": errors}, status=400)

    saved_note = form.save()
    return JsonResponse(
        {
            "status": "saved",
            "updated_at": saved_note.updated_at.isoformat(),
            "display_time": saved_note.updated_at.strftime("%b %-d, %Y, %-I:%M %p"),
        }
    )


@login_required
def note_export(request: HttpRequest, pk: int) -> HttpResponse:
    """Download a note as a UTF-8 text file."""
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    content = f"{note.title}\n{note.updated_at:%Y-%m-%d %H:%M UTC}\n\n{note.body}"
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    safe_name = slugify(note.title) or f"note-{note.pk}"
    response["Content-Disposition"] = f'attachment; filename="{safe_name}.txt"'
    return response


@login_required
def note_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Confirm and delete a note owned by the current user."""
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == "POST":
        note.delete()
        return redirect("notes:list")
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])
    return render(request, "notes/note_confirm_delete.html", {"note": note})
