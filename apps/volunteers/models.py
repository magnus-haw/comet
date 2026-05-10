from django.db import models

# Create your models here.
    
class VolunteerOpportunity(models.Model):

    CATEGORY_CHOICES = [
        ("classroom", "Classroom"),
        ("board", "Board"),
        ("comittee", "Committees"),
        ("event", "Event"),
        ("maintenance", "Maintenance"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=255)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="other",
    )

    description = models.TextField(blank=True)

    event_date = models.DateField(
        null=True,
        blank=True,
    )

    expected_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        "people.Staff",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Volunteer Opportunity"
        verbose_name_plural = "Volunteer Opportunities"
        ordering = ["-event_date", "-created_at"]

    def __str__(self):
        return self.title


class VolunteerEntry(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    household = models.ForeignKey(
        "people.Household",
        on_delete=models.CASCADE,
        related_name="volunteer_hours",
    )

    parent = models.ForeignKey(
        "people.Parent",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    service_date = models.DateField()

    hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
    )

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ["-service_date", "-created_at"]
        verbose_name_plural = "Volunteer Entries"

    def __str__(self):
        return f"{self.household} - {self.hours} hrs"
