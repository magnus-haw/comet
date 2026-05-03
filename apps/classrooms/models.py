from django.db import models
from apps.people.models import Staff
from decimal import Decimal

DEPARTMENTS = [
    ("IN", "Infant"),
    ("TL", "Toddler"),
    ("TR", "Preschool Transition"),
    ("PS", "Preschool"),
]



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
    
    

    
