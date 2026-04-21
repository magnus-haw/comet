from django.db import models


HOUSEHOLD_TYPES = [
    ("CV", "Civil Servant"),
    ("P", "Public"),
    ("S", "Staff"),
    ("M", "Military"),
]


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



