from django.contrib import admin
from .models import Household, Parent, Child, Staff


class ParentInline(admin.TabularInline):
    model = Parent
    extra = 1


class ChildInline(admin.TabularInline):
    model = Child
    extra = 1


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "household_type", "phone_number")
    search_fields = ("name", "address")

    inlines = [ParentInline, ChildInline]


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "household")
    search_fields = ("first_name", "last_name", "email")


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "birth_date", "household", "enrolled")
    list_filter = ("enrolled",)
    search_fields = ("first_name", "last_name")


class StaffAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "role", "email")
    list_filter = ("role",)
    search_fields = ("first_name", "last_name", "email")
    ordering = ("last_name", "first_name")




