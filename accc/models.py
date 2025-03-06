from django.db import models
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from datetime import date
from dateutil.relativedelta import relativedelta

# Defined move-up age thresholds in months
MOVE_UP_AGE_THRESHOLDS = [12, 18, 30, 42, 48, 60]
HOUSEHOLD_TYPES = [
        ("CV", "Civil Servant"),
        ("P", "Public"),
        ("M", "Military"),
    ]

class HouseholdManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)
    
class Household(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    household_type = models.CharField(
        max_length=2, 
        choices=HOUSEHOLD_TYPES, 
        default="P",
        help_text="Classify the household type."
    )
    objects = HouseholdManager()  # Use custom manager

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

class Parent(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="parents")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class VolunteerHours(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="hours")
    date = models.DateField()
    value = models.PositiveIntegerField(help_text="Hours volunteered")

    def __str__(self):
        return f"{self.household} {self.date}: {self.value}"

class RoomManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

class Room(models.Model):
    ROOM_CATEGORIES = [
        ("infant", "Infant (0-12 months)"),
        ("young_toddler", "Young Toddler (12-18 months)"),
        ("toddler", "Toddler (18-30 months)"),
        ("transitional_preschool", "Transitional Preschool (30-48 months)"),
        ("preschool", "Preschool (48-60 months)"),
    ]

    name = models.CharField(max_length=100, unique=True)
    min_age = models.PositiveIntegerField(help_text="Minimum age in months")
    max_age = models.PositiveIntegerField(help_text="Maximum age in months")
    capacity = models.PositiveIntegerField(help_text="Number of children allowed")
    tuition_rate = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(
        max_length=30,
        choices=ROOM_CATEGORIES,
        blank=True,
        help_text="Categorization based on age range"
    )
    objects = RoomManager()  # Use custom manager

    def natural_key(self):
        return (self.name,)

    def save(self, *args, **kwargs):
        """Auto-assign room category based on age range"""
        if self.min_age < 12:
            self.category = "infant"
        elif self.min_age < 18:
            self.category = "young_toddler"
        elif self.min_age < 30:
            self.category = "toddler"
        elif self.min_age < 42:
            self.category = "transitional_preschool"
        elif self.min_age < 48:
            self.category = "early_preschool"
        else:
            self.category = "preschool"

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["min_age"]

    def __str__(self):
        return f"{self.name} - {dict(self.ROOM_CATEGORIES).get(self.category, 'Unknown')}"

class ChildManager(models.Manager):
    def get_by_natural_key(self, first_name, last_name, birth_date):
        return self.get(first_name=first_name, last_name=last_name, birth_date=birth_date)

class Child(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="children")
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    accc_enroll_date = models.DateField(blank=True, null=True)
    expected_move_up_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="children")

    objects = ChildManager()  # Use custom manager

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def natural_key(self):
        return (self.first_name, self.last_name, self.birth_date)

    class Meta:
        unique_together = (("first_name", "last_name", "birth_date"),)
        verbose_name_plural = "Children"
    
    def set_expected_move_up_date(self):
        """Determines the expected move-up date based on the max age of the child's current room."""
        if not self.birth_date or not self.room:
            return None  # Cannot calculate without birthdate or room

        today = timezone.now().date()  # Timezone-aware version of today
        sept_1st_this_year = date(today.year, 9, 1)

        # Calculate child's age in months as of May 15 of the current year
        months_old_on_sept1 = (sept_1st_this_year.year - self.birth_date.year) * 12 + (9 - self.birth_date.month)

        # if self.room.name == "VANGUARD" and months_old_on_sept1 > 60:
        #     # If child will be >60 months old by Sept 1, set move-up date to May 15
        #     move_up_date = sept_1st_this_year
        # else:
        #     # Calculate the date when the child reaches the max age for their current room
        move_up_date = self.birth_date + relativedelta(months=self.room.max_age)

        # Update the child's expected move-up date
        self.expected_move_up_date = move_up_date
        self.save()
        return move_up_date

    def save(self, *args, **kwargs):
        """Override save method"""
        # if not self.expected_move_up_date:
        #     self.set_expected_move_up_date()
        super().save(*args, **kwargs)


class RoomTransition(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="room_transitions")
    current_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="transitions")
    new_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="new_transitions")
    teacher_assessment = models.TextField(null=True, blank=True)
    start_date = models.DateField()
    sent_transition_email = models.BooleanField(default=False)
    parents_agree = models.BooleanField(default=False)
    updated_procare = models.BooleanField(default=False)
    updated_db = models.BooleanField(default=False)
    updated_tuition_rate = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.child} - {self.new_room} ({self.start_date})"

    class Meta:
        verbose_name_plural = "Room Transitions"
        unique_together = ('child','current_room',)
        ordering = ("start_date",)
    
    @property
    def is_complete(self):
        return self.parents_agree and self.updated_procare and self.updated_db and self.updated_tuition_rate and now().date() >= self.start_date

    def mark_complete(self):
        """Marks the transition process as complete if all conditions are met."""
        if self.is_complete:
            self.complete = True
            self.child.room = self.new_room
            self.child.set_expected_move_up_date()
            self.child.save()
            self.save()

    def send_transition_email(self):
        """Sends an email notification to the parents when a transition is initiated."""
        if not self.sent_transition_email:
            subject = f"Room Transition Notice for {self.child.first_name} {self.child.last_name}"
            message = (
                f"Dear Parents,\n\n"
                f"Your child {self.child.first_name} is scheduled to transition from {self.current_room} "
                f"to {self.new_room} on {self.start_date}.\n\n"
                f"Please confirm your agreement.\n\nBest,\nSchool Administration"
            )
            recipients = [self.child.household.parents.all().values_list('email', flat=True)]
            send_mail(subject, message, 'admin@ameschildcare.org', recipients)
            self.sent_transition_email = True
            self.save()


class NewEnrollment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="enrollments")
    accepted = models.BooleanField(default=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="newenrollments")
    teacher_assessment = models.TextField(null=True, blank=True)
    start_date = models.DateField()
    sent_welcome_email = models.BooleanField(default=False)
    parents_agree = models.BooleanField(default=False)
    add_to_procare = models.BooleanField(default=False)
    add_to_db = models.BooleanField(default=False)
    security_deposit = models.BooleanField(default=False)
    child_files = models.BooleanField(default=False)
    parentemail1 = models.EmailField(null=True, blank=True)
    parentemail2 = models.EmailField(null=True, blank=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.child} - {self.room} ({self.start_date})"

    class Meta:
        unique_together = ('child','room',)

    def is_fully_processed(self):
        """Checks if all required steps for enrollment are completed."""
        return all([self.accepted, self.add_to_procare, self.add_to_db, self.security_deposit, self.child_files])

    def send_welcome_email(self):
        """Sends a welcome email to the parents if not already sent."""
        if not self.sent_welcome_email:
            subject = f"Welcome to {self.room.name}, {self.child.first_name}!"
            message = (
                f"Dear Parents,\n\n"
                f"We are excited to welcome {self.child.first_name} to {self.room.name} starting {self.start_date}.\n"
                f"Please ensure all required documents are submitted.\n\nBest,\nSchool Administration"
            )
            recipients = [email for email in [self.parentemail1, self.parentemail2] if email]
            if recipients:
                send_mail(subject, message, 'admin@school.com', recipients)
                self.sent_welcome_email = True
                self.save()


class Withdrawals(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="withdrawals")
    accepted = models.BooleanField(default=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="room_withdrawals")
    teacher_assessment = models.TextField(null=True, blank=True)
    start_date = models.DateField()
    sent_welcome_email = models.BooleanField(default=False)
    parents_agree = models.BooleanField(default=False)
    add_to_procare = models.BooleanField(default=False)
    add_to_db = models.BooleanField(default=False)
    security_deposit = models.BooleanField(default=False)
    child_files = models.BooleanField(default=False)
    parentemail1 = models.EmailField(null=True, blank=True)
    parentemail2 = models.EmailField(null=True, blank=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.child} - {self.room} ({self.start_date})"

    class Meta:
        unique_together = ('child','room',)

    def is_fully_processed(self):
        """Checks if all required steps for withdrawal are completed."""
        return all([self.accepted, self.remove_from_procare, self.remove_from_db, self.refund_security_deposit, self.remove_child_files])

    def send_exit_email(self):
        """Sends an exit confirmation email to the parents."""
        if not self.sent_exit_email:
            subject = f"Withdrawal Confirmation for {self.child.first_name} {self.child.last_name}"
            message = (
                f"Dear Parents,\n\n"
                f"We confirm that {self.child.first_name} will be withdrawn from {self.room.name} "
                f"effective {self.start_date}.\n\n"
                f"If you have any questions, please contact us.\n\nBest,\nSchool Administration"
            )
            recipients = [email for email in [self.parentemail1, self.parentemail2] if email]
            if recipients:
                send_mail(subject, message, 'admin@school.com', recipients)
                self.sent_exit_email = True
                self.save()


class Waitlist(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="waitlist_entries")
    date_added = models.DateTimeField(default=timezone.now)
    priority = models.PositiveIntegerField(default=1, help_text="Lower number = higher priority")

    class Meta:
        ordering = ["priority", "date_added"]

    def __str__(self):
        return f"{self.child} - (Priority {self.priority})"


class Staff(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    infant_certification = models.BooleanField(default=False)
    teacher_certification = models.BooleanField(default=False)
    role = models.CharField(max_length=100, choices=[
        ("teacher", "Teacher"),
        ("floater", "Floater"),
        ("chef", "Chef"),
        ("director", "Director"),
        ("admin", "Administrator")
    ])
    primary_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, related_name="primary_staff")
    other_rooms = models.ManyToManyField(Room, blank=True, related_name="additional_staff")
    work_hours = models.CharField(max_length=50, help_text="E.g., Mon-Fri 8am-4pm")

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.role}"

    class Meta:
        verbose_name_plural = "Staff"