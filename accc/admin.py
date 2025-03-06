from django.contrib import admin
from django.core.mail import send_mail
from django.utils.html import format_html
from .models import Household, Parent, Room, Child, RoomTransition
from .models import Waitlist, Staff, Withdrawals, NewEnrollment
from django.contrib.admin import AdminSite

# Customize the admin site headers and titles
admin.site.site_header = "COMET Admin"
admin.site.site_title = "COMET Admin"
admin.site.index_title = "Welcome to ACCC Child Care Management"

# Register each model in the Django admin
@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "household_type", "address", "phone_number")
    list_filter = ("household_type",)
    search_fields = ("name", "address")


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "household")
    search_fields = ("first_name", "last_name", "email")
    list_filter = ("household",)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "min_age", "max_age", "capacity")
    list_filter = ("category",)
    search_fields = ("name",)

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "birth_date", "room", "expected_move_up_date")
    search_fields = ("first_name", "last_name")
    list_filter = ("room",)
    ordering = ("birth_date",)

@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ("child", "date_added", "priority")
    list_filter = ("priority",)
    ordering = ("priority", "date_added")

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "role", "primary_room", "salary")
    search_fields = ("first_name", "last_name", "email")
    list_filter = ("role", "primary_room")

@admin.register(RoomTransition)
class RoomTransitionAdmin(admin.ModelAdmin):
    list_display = ("child", "current_room", "new_room", "start_date", "complete")
    list_filter = ("complete", "current_room", "new_room")
    search_fields = ("child__first_name", "child__last_name", "current_room__name", "new_room__name")


@admin.register(NewEnrollment)
class NewEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("child", "room", "start_date", "accepted", "send_welcome_email_button", "process_enrollment_button")
    list_filter = ("accepted", "room")
    search_fields = ("child__first_name", "child__last_name", "room__name")

    def send_welcome_email_button(self, obj):
        """Displays a button to send welcome email"""
        if not obj.sent_welcome_email:
            return format_html('<a class="button" href="/admin/send-welcome-email/{}/">📧 Send Welcome Email</a>', obj.id)
        return "✅ Email Sent"

    send_welcome_email_button.allow_tags = True
    send_welcome_email_button.short_description = "Send Email"

    def process_enrollment_button(self, obj):
        """Displays a button to mark enrollment as fully processed"""
        if not obj.is_fully_processed():
            return format_html('<a class="button" href="/admin/process-enrollment/{}/">✔ Process</a>', obj.id)
        return "✅ Processed"

    process_enrollment_button.allow_tags = True
    process_enrollment_button.short_description = "Process Enrollment"

    actions = ["send_welcome_emails", "process_enrollments"]

    def send_welcome_emails(self, request, queryset):
        """Send welcome emails to selected enrollments"""
        for enrollment in queryset:
            enrollment.send_welcome_email()
        self.message_user(request, "Welcome emails sent successfully.")
    
    def process_enrollments(self, request, queryset):
        """Mark selected enrollments as fully processed"""
        for enrollment in queryset:
            enrollment.add_to_db = True
            enrollment.add_to_procare = True
            enrollment.security_deposit = True
            enrollment.child_files = True
            enrollment.accepted = True
            enrollment.save()
        self.message_user(request, "Selected enrollments processed.")

    send_welcome_emails.short_description = "Send welcome emails"
    process_enrollments.short_description = "Mark enrollments as processed"


@admin.register(Withdrawals)
class WithdrawalsAdmin(admin.ModelAdmin):
    list_display = ("child", "room", "start_date", "accepted", "send_exit_email_button", "process_withdrawal_button")
    list_filter = ("accepted", "room")
    search_fields = ("child__first_name", "child__last_name", "room__name")

    def send_exit_email_button(self, obj):
        """Displays a button to send exit email"""
        if not obj.sent_exit_email:
            return format_html('<a class="button" href="/admin/send-exit-email/{}/">📧 Send Exit Email</a>', obj.id)
        return "✅ Email Sent"

    send_exit_email_button.allow_tags = True
    send_exit_email_button.short_description = "Send Email"

    def process_withdrawal_button(self, obj):
        """Displays a button to mark withdrawal as fully processed"""
        if not obj.is_fully_processed():
            return format_html('<a class="button" href="/admin/process-withdrawal/{}/">✔ Process</a>', obj.id)
        return "✅ Processed"

    process_withdrawal_button.allow_tags = True
    process_withdrawal_button.short_description = "Process Withdrawal"

    actions = ["send_exit_emails", "process_withdrawals"]

    def send_exit_emails(self, request, queryset):
        """Send exit emails to selected withdrawals"""
        for withdrawal in queryset:
            withdrawal.send_exit_email()
        self.message_user(request, "Exit emails sent successfully.")
    
    def process_withdrawals(self, request, queryset):
        """Mark selected withdrawals as fully processed"""
        for withdrawal in queryset:
            withdrawal.remove_from_db = True
            withdrawal.remove_from_procare = True
            withdrawal.refund_security_deposit = True
            withdrawal.remove_child_files = True
            withdrawal.accepted = True
            withdrawal.save()
        self.message_user(request, "Selected withdrawals processed.")

    send_exit_emails.short_description = "Send exit emails"
    process_withdrawals.short_description = "Mark withdrawals as processed"