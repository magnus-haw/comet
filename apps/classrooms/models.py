from django.db import models
from django.db.models import Q
from apps.people.models import Staff
from decimal import Decimal

DEPARTMENTS = [
    ("IN", "Infant"),
    ("TL", "Toddler"),
    ("TR", "Preschool Transition"),
    ("PS", "Preschool"),
]

from django.utils.timezone import now

class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)

    capacity = models.PositiveIntegerField()

    min_age_months = models.PositiveIntegerField(
        help_text="Minimum age in months"
    )

    max_age_months = models.PositiveIntegerField(
        help_text="Maximum age in months"
    )
    
    department = models.CharField(
        max_length=2,
        choices=DEPARTMENTS,
        default="PS",
    )

    primary_teachers = models.ManyToManyField(
        Staff,
        blank=True,
        related_name="primary_rooms",
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
    def occupancy(self, target_date):
        today = now().date()

        # -------------------------
        # 1. Base occupancy
        # -------------------------
        occupants = set(
            self.placements
            .filter(start_date__lte=target_date)
            .filter(Q(end_date__isnull=True) | Q(end_date__gt=target_date))
            .values_list("child_id", flat=True)
        )

        # -------------------------
        # 2. Past or present
        # -------------------------
        if target_date <= today:
            return len(occupants)

        # -------------------------
        # 3. Relevant plans (room-scoped)
        # -------------------------
        plans = list(
            self.moveups_from.filter(
                status="planned",
                planned_date__isnull=False,
                planned_date__gt=today,
                planned_date__lte=target_date,
            )
        ) + list(
            self.incoming_moveups.filter(
                status="planned",
                planned_date__isnull=False,
                planned_date__gt=today,
                planned_date__lte=target_date,
            )
        )

        # Optional: dedupe (defensive)
        plans = {p.id: p for p in plans}.values()

        # -------------------------
        # 4. Apply plans
        # -------------------------
        for plan in plans:
            child_id = plan.child_id

            if plan.current_room_id == self.id:
                occupants.discard(child_id)

            if plan.exit_type == "moveup" and plan.target_room_id == self.id:
                occupants.add(child_id)

            if plan.exit_type in ["withdrawal", "graduation"]:
                if plan.current_room_id == self.id:
                    occupants.discard(child_id)

        return len(occupants)





