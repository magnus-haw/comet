from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from apps.classrooms.models import Room
from apps.people.models import Child, Household
from .projections import add_months, kindergarten_year, build_kindergarten_cohorts, child_planning_detail
from .dashboard_logic import build_dashboard_data, build_global_stats, get_center_occupancy_projections
from .models import MoveUpPlan, Placement


class PlanningRegressionTests(TestCase):
    def setUp(self):
        self.today = now().date()
        self.household = Household.objects.create(name="Test Household")
        self.room_a = Room.objects.create(
            name="Room A", capacity=10, min_age_months=0, max_age_months=36, department="IN"
        )
        self.room_b = Room.objects.create(
            name="Room B", capacity=10, min_age_months=18, max_age_months=60, department="TL"
        )
        self.child = Child.objects.create(
            household=self.household,
            first_name="Test",
            last_name="Child",
            birth_date=add_months(self.today, -24),
        )
        self.user = get_user_model().objects.create_user(username="tester", password="testpass")
        self.client.force_login(self.user)

    def test_future_enrollment_not_counted_today_but_counted_in_projection(self):
        Placement.objects.create(
            child=self.child,
            room=self.room_a,
            start_date=self.today + timedelta(days=20),
        )

        stats = build_global_stats()
        room_data = build_dashboard_data(room_ids=[self.room_a.id])[0]
        projections = get_center_occupancy_projections()

        self.assertEqual(stats["total_children"], 0)
        self.assertEqual(room_data["occupancy"], 0)
        self.assertEqual(projections["plus_30"]["children"], 1)

    def test_implemented_move_uses_planned_date_for_placement_history(self):
        source = Placement.objects.create(
            child=self.child,
            room=self.room_a,
            start_date=self.today - timedelta(days=60),
        )
        effective_date = self.today - timedelta(days=1)
        plan = MoveUpPlan.objects.create(
            child=self.child,
            current_room=self.room_a,
            target_room=self.room_b,
            planned_date=effective_date,
            exit_type="moveup",
            status="planned",
        )

        response = self.client.post(reverse("implement-moveup", args=[plan.id]))
        self.assertEqual(response.status_code, 200)

        source.refresh_from_db()
        plan.refresh_from_db()
        new_placement = Placement.objects.get(child=self.child, room=self.room_b)

        self.assertEqual(source.end_date, effective_date)
        self.assertEqual(new_placement.start_date, effective_date)
        self.assertEqual(plan.status, "completed")

    def test_future_dated_implemented_move_keeps_source_room_current_until_effective_date(self):
        Placement.objects.create(
            child=self.child,
            room=self.room_a,
            start_date=self.today - timedelta(days=60),
        )
        effective_date = self.today + timedelta(days=2)
        plan = MoveUpPlan.objects.create(
            child=self.child,
            current_room=self.room_a,
            target_room=self.room_b,
            planned_date=effective_date,
            exit_type="moveup",
            status="planned",
        )

        self.client.post(reverse("implement-moveup", args=[plan.id]))

        room_a_data = build_dashboard_data(room_ids=[self.room_a.id])[0]
        room_b_data = build_dashboard_data(room_ids=[self.room_b.id])[0]
        self.assertEqual(room_a_data["occupancy"], 1)
        self.assertEqual(room_b_data["occupancy"], 0)

    def test_kindergarten_cutoff(self):
        self.assertEqual(kindergarten_year(self.today.replace(year=2021, month=8, day=31)), 2026)
        self.assertEqual(kindergarten_year(self.today.replace(year=2021, month=9, day=1)), 2027)
        self.assertEqual(kindergarten_year(self.today.replace(year=2021, month=9, day=2)), 2027)

    def test_child_planning_uses_earliest_placement_as_center_enrollment_date(self):
        first_start = self.today - timedelta(days=200)
        Placement.objects.create(child=self.child, room=self.room_a, start_date=first_start, end_date=self.today - timedelta(days=30))
        Placement.objects.create(child=self.child, room=self.room_b, start_date=self.today - timedelta(days=30))

        detail = child_planning_detail(self.child)

        self.assertEqual(detail["center_enrollment_date"], first_start)
        self.assertEqual(detail["placement"].room, self.room_b)

    def test_planning_overview_route_is_available(self):
        response = self.client.get(reverse("planning-overview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Center Planning")

    def test_child_planning_route_is_available(self):
        Placement.objects.create(child=self.child, room=self.room_a, start_date=self.today - timedelta(days=10))
        response = self.client.get(reverse("child-planning", args=[self.child.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Age milestones")
