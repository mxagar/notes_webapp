"""URL configuration for note operations."""

from django.urls import path

from . import views

app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("new/", views.note_create, name="create"),
    path("<int:pk>/", views.note_edit, name="edit"),
    path("<int:pk>/autosave/", views.note_autosave, name="autosave"),
    path("<int:pk>/export/", views.note_export, name="export"),
    path("<int:pk>/delete/", views.note_delete, name="delete"),
]
