from django.db import models

from apps.people.models import Child
from apps.classrooms.models import Room
from .utils import HOUSEHOLD_PRIORITY

class Placement(models.Model):
    """
    The authoritative record of where a child is assigned.
    """

    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="placements",
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="placements",
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.child} → {self.room}"

    @property
    def is_current(self):
        return self.end_date is None

class MoveUpPlan(models.Model):
    """
    Planning record for potential classroom transitions.
    This is editable and advisory.
    """
    EXIT_CHOICES = [
        ("moveup", "Move Up"),
        ("graduation", "Graduation"),
        ("withdrawal", "Withdrawal"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("planned", "Planned"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="moveup_plans",
    )

    current_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moveups_from",
    )

    target_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_moveups",
    )

    earliest_date = models.DateField(
        null=True,
        blank=True,
        help_text="Earliest possible move-up date",
    )

    planned_date = models.DateField(
        null=True,
        blank=True,
        help_text="Director planned move date",
    )

    readiness_level = models.IntegerField(
        null=True,
        blank=True,
        help_text="Teacher readiness score (1-5)",
    )
    exit_type = models.CharField(
        max_length=20,
        choices=EXIT_CHOICES,
        default="moveup",
    )

    teacher_notes = models.TextField(blank=True)
    director_notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["planned_date"]

    def __str__(self):
        return f"MoveUpPlan: {self.child}"


class WaitlistEntry(models.Model):

    child = models.ForeignKey(
        "people.Child",
        on_delete=models.CASCADE
    )

    requested_start = models.DateField()

    preferred_rooms = models.ManyToManyField(
        "classrooms.Room",
        blank=True
    )

    priority_score = models.IntegerField(default=0)

    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("waiting", "Waiting"),
            ("planned", "Planned"),
            ("enrolled", "Enrolled"),
            ("withdrawn", "Withdrawn"),
        ],
        default="waiting",
    )
    
    def priority_score(self):
        household_type = self.child.household.household_type
        base_priority = HOUSEHOLD_PRIORITY.get(household_type, 0)
        return base_priority

class AdmissionPlan(models.Model):

    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("implemented", "Implemented"),
        ("cancelled", "Cancelled"),
    ]

    waitlist_entry = models.ForeignKey(
        "planning.WaitlistEntry",
        on_delete=models.CASCADE,
        related_name="admission_plans"
    )

    child = models.ForeignKey(
        "people.Child",
        on_delete=models.CASCADE
    )

    target_room = models.ForeignKey(
        "classrooms.Room",
        on_delete=models.CASCADE
    )

    planned_date = models.DateField()

    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planned"
    )

    created_at = models.DateTimeField(auto_now_add=True)



