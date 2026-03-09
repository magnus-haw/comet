from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="planning-dashboard"),

    path(
        "moveup-form/<int:child_id>/",
        views.moveup_form,
        name="moveup-form",
    ),

    path(
        "create-moveup/",
        views.create_moveup,
        name="create-moveup",
    ),
    path(
    "edit-moveup/<int:plan_id>/",
    views.edit_moveup_form,
    name="edit-moveup-form",
    ),

    path(
        "update-moveup/<int:plan_id>/",
        views.update_moveup,
        name="update-moveup",
    ),

    path(
        "cancel-moveup/<int:plan_id>/",
        views.cancel_moveup,
        name="cancel-moveup",
    ),
    path(
        "implement-moveup/<int:plan_id>/",
        views.implement_moveup,
        name="implement-moveup",
    ),

]
