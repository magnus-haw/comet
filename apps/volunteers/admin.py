from django.contrib import admin

# Register your models here.

from .models import (
    VolunteerOpportunity,
    VolunteerEntry,
)

@admin.register(VolunteerOpportunity)
class VolunteerOpportunityAdmin(admin.ModelAdmin):

    list_display = [
        "title",
        "category",
        "event_date",
        "expected_hours",
        "is_active",
    ]

    list_filter = [
        "category",
        "is_active",
    ]

    search_fields = [
        "title",
        "description",
    ]

    ordering = [
        "-event_date",
        "title",
    ]

@admin.register(VolunteerEntry)
class VolunteerHoursAdmin(admin.ModelAdmin):

    list_display = [
        "service_date",
        "description",
        "household",
        "parent",
        "hours",
        "status",
    ]

    list_filter = [
        "status",
        "service_date",
    ]

    search_fields = [
        "household__name",
        "parent__first_name",
        "parent__last_name",
        "description",
    ]

    autocomplete_fields = [
        "household",
        "parent",
    ]

    ordering = [
        "-service_date",
        "-created_at",
    ]

    readonly_fields = [
        "created_at",
        "reviewed_at",
    ]
    
    list_editable = [
        "status",
    ]

    actions = [
        "approve_selected",
        "reject_selected",
    ]
    
    
    def description_short(self, obj):

        if len(obj.description) > 50:

            return obj.description[:50] + "..."

        return obj.description

    description_short.short_description = (
        "Description"
    )

    @admin.action(description="Approve selected submissions")
    def approve_selected(
        self,
        request,
        queryset,
    ):

        from django.utils import timezone

        queryset.update(
            status="approved",
            reviewed_at=timezone.now(),
        )

    @admin.action(description="Reject selected submissions")
    def reject_selected(
        self,
        request,
        queryset,
    ):

        from django.utils import timezone

        queryset.update(
            status="rejected",
            reviewed_at=timezone.now(),
        )

