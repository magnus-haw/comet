from django.contrib import admin

from .models import Placement, MoveUpPlan, WaitlistEntry


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):

    list_display = (
        "child",
        "room",
        "start_date",
        "end_date",
    )

    list_filter = (
        "room",
    )

    search_fields = (
        "child__first_name",
        "child__last_name",
    )


@admin.register(MoveUpPlan)
class MoveUpPlanAdmin(admin.ModelAdmin):

    list_display = (
        "child",
        "current_room",
        "target_room",
        "planned_date",
        "status",
    )

    list_filter = (
        "status",
        "current_room",
        "target_room",
    )

    search_fields = (
        "child__first_name",
        "child__last_name",
    )


from django.contrib import admin
from .models import WaitlistEntry


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):

    list_display = (
        "child",
        "household_type",
        "requested_start",
        "priority",
        "status",
    )

    list_filter = (
        "status",
        "child__household__household_type",
        "requested_start",
    )

    search_fields = (
        "child__first_name",
        "child__last_name",
        "child__household__name",
    )

    ordering = (
        "-child__household__household_type",
        "requested_start",
    )

    autocomplete_fields = (
        "child",
    )

    readonly_fields = (
        "priority",
    )

    def household_type(self, obj):
        return obj.child.household.get_household_type_display()

    household_type.short_description = "Household Type"

    def priority(self, obj):
        return obj.priority_score()

    priority.short_description = "Priority Score"
    








