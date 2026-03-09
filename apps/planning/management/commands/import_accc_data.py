import sqlite3
from django.core.management.base import BaseCommand

from apps.people.models import Household, Parent, Child, Staff
from apps.classrooms.models import Room
from apps.planning.models import Placement, MoveUpPlan, WaitlistEntry

from django.conf import settings
from datetime import date


OLD_DB = "_db.sqlite3"  # rename your uploaded DB file


class Command(BaseCommand):
    help = "Import data from old ACCC schema into new schema"

    def handle(self, *args, **kwargs):

        conn = sqlite3.connect(OLD_DB)
        cursor = conn.cursor()

        self.stdout.write("Importing households...")

        for row in cursor.execute("SELECT id, name, address, phone_number, household_type FROM accc_household"):
            old_id, name, address, phone, htype = row

            Household.objects.create(
                id=old_id,
                name=name,
                address=address or "",
                phone_number=phone or "",
                household_type=htype or "P",
            )

        self.stdout.write("Importing parents...")

        for row in cursor.execute("""
            SELECT id, first_name, last_name, email, phone_number, household_id
            FROM accc_parent
        """):

            Parent.objects.create(
                id=row[0],
                first_name=row[1],
                last_name=row[2],
                email=row[3],
                phone_number=row[4] or "",
                household_id=row[5],
            )

        self.stdout.write("Importing children...")

        for row in cursor.execute("""
            SELECT id, first_name, last_name, birth_date, household_id, enrolled, notes
            FROM accc_child
        """):

            Child.objects.create(
                id=row[0],
                first_name=row[1],
                last_name=row[2],
                birth_date=row[3],
                household_id=row[4],
                enrolled=row[5],
                notes=row[6] or "",
            )

        self.stdout.write("Importing rooms...")

        for row in cursor.execute("""
            SELECT id, name, capacity, min_age, max_age
            FROM accc_room
        """):

            Room.objects.create(
                id=row[0],
                name=row[1],
                capacity=row[2],
                min_age_months=row[3],
                max_age_months=row[4],
            )

        self.stdout.write("Creating placements...")

        for row in cursor.execute("""
            SELECT id, room_id, accc_enroll_date
            FROM accc_child
            WHERE room_id IS NOT NULL
        """):

            child_id = row[0]
            room_id = row[1]
            start = row[2] or date.today()

            Placement.objects.create(
                child_id=child_id,
                room_id=room_id,
                start_date=start,
            )

        self.stdout.write("Importing waitlist...")

        for row in cursor.execute("""
            SELECT child_id, priority
            FROM accc_waitlist
        """):

            WaitlistEntry.objects.create(
                child_id=row[0],
                priority=row[1],
            )

        self.stdout.write("Importing move-up plans...")

        for row in cursor.execute("""
            SELECT child_id, current_room_id, new_room_id, start_date
            FROM accc_roomtransition
        """):

            MoveUpPlan.objects.create(
                child_id=row[0],
                current_room_id=row[1],
                target_room_id=row[2],
                planned_date=row[3],
                status="planned",
            )

        self.stdout.write(self.style.SUCCESS("Import completed."))



