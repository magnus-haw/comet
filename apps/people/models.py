from django.db import models
from decimal import Decimal

HOUSEHOLD_TYPES = [
    ("CV", "Civil Servant"),
    ("P", "Public"),
    ("S", "Staff"),
    ("M", "Military"),
]

TUITION_RATES = {
    # -----------------------
    # Civil Servant (NASA)
    # -----------------------
    ("IN", "CV"): Decimal("1380.12"),
    ("TL", "CV"): Decimal("1341.17"),
    ("TR", "CV"): Decimal("1213.17"),
    ("PS", "CV"): Decimal("978.33"),

    # -----------------------
    # Military (same as NASA)
    # -----------------------
    ("IN", "M"): Decimal("1380.12"),
    ("TL", "M"): Decimal("1341.17"),
    ("TR", "M"): Decimal("1213.17"),
    ("PS", "M"): Decimal("978.33"),

    # -----------------------
    # Staff (10% discount vs NASA)
    # -----------------------
    ("IN", "S"): Decimal("1242.11"),  # 1380.12 * 0.9
    ("TL", "S"): Decimal("1207.05"),  # 1341.17 * 0.9
    ("TR", "S"): Decimal("1091.85"),  # 1213.17 * 0.9
    ("PS", "S"): Decimal("880.50"),   # 978.33 * 0.9

    # -----------------------
    # Public
    # -----------------------
    ("IN", "P"): Decimal("1536.85"),
    ("TL", "P"): Decimal("1493.74"),
    ("TR", "P"): Decimal("1357.64"),
    ("PS", "P"): Decimal("1100.17"),
}

class Household(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    household_type = models.CharField(
        max_length=2,
        choices=HOUSEHOLD_TYPES,
        default="P",
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Parent(models.Model):
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="parents",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    is_primary_contact = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Child(models.Model):
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="children",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    enrolled = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Security deposit (stored, editable, defaulted)
    security_deposit = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("1380.12"),
    )

    # Tuition override (null = auto)
    tuition_override = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("first_name", "last_name", "birth_date")
        verbose_name_plural = "Children"
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age_months(self):
        from datetime import date

        today = date.today()
        return (today.year - self.birth_date.year) * 12 + (today.month - self.birth_date.month)
    
    @property
    def tuition(self):
        if self.tuition_override is not None:
            return self.tuition_override

        return self.calculate_tuition()
    
    def calculate_tuition(self):
        placement = (
            self.placements
            .filter(end_date__isnull=True)
            .select_related("room")
            .first()
        )

        if not placement:
            return None

        household_type = self.household.household_type
        room = placement.room
        
        return TUITION_RATES.get((room.department, household_type))

class Staff(models.Model):

    ROLES = [
        ("teacher", "Teacher"),
        ("floater", "Floater"),
        ("chef", "Chef"),
        ("director", "Director"),
        ("admin", "Administrator"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=50,
        choices=ROLES,
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



