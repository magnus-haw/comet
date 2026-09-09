import calendar
from collections import defaultdict
from datetime import date, timedelta

from django.db.models import Q
from django.utils.timezone import now

from apps.classrooms.models import Room
from apps.people.models import Child
from .models import MoveUpPlan, Placement


MILESTONES = [
    ("12 months", 12),
    ("18 months", 18),
    ("2 years", 24),
    ("30 months", 30),
    ("3 years", 36),
    ("4 years", 48),
    ("5 years", 60),
]


def add_months(value, months):
    """Add calendar months while clamping to the destination month's last day."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def kindergarten_year(birth_date):
    """Return the fall kindergarten year using a strict September 1 cutoff.

    A child must already be five before September 1. A fifth birthday on
    September 1 therefore belongs to the following year's kindergarten class.
    """
    fifth_birthday = add_months(birth_date, 60)
    cutoff = date(fifth_birthday.year, 9, 1)
    return fifth_birthday.year if fifth_birthday < cutoff else fifth_birthday.year + 1


def current_placement_for(child, target_date=None):
    target_date = target_date or now().date()
    return (
        child.placements.select_related("room")
        .filter(start_date__lte=target_date)
        .filter(Q(end_date__isnull=True) | Q(end_date__gt=target_date))
        .order_by("-start_date")
        .first()
    )


def center_enrollment_date(child):
    first = child.placements.order_by("start_date").first()
    return first.start_date if first else None


def child_milestones(child):
    return [
        {"label": label, "date": add_months(child.birth_date, months), "months": months}
        for label, months in MILESTONES
    ]


def child_planning_detail(child):
    today = now().date()
    placement = current_placement_for(child, today)
    active_plan = (
        child.moveup_plans.select_related("current_room", "target_room")
        .filter(status="planned")
        .order_by("planned_date")
        .first()
    )
    history = child.placements.select_related("room").order_by("start_date")

    return {
        "child": child,
        "today": today,
        "placement": placement,
        "center_enrollment_date": center_enrollment_date(child),
        "kindergarten_year": kindergarten_year(child.birth_date),
        "milestones": child_milestones(child),
        "active_plan": active_plan,
        "placement_history": history,
    }


def build_kindergarten_cohorts():
    groups = defaultdict(list)
    children = Child.objects.filter(enrolled=True).order_by("birth_date", "last_name", "first_name")
    for child in children:
        groups[kindergarten_year(child.birth_date)].append(child)

    return [
        {
            "year": year,
            "children": rows,
            "count": len(rows),
            "capacity": 20,
            "open_spots": 20 - len(rows),
            "over_capacity": len(rows) > 20,
        }
        for year, rows in sorted(groups.items())
    ]


def build_center_room_projection(target_dates=None):
    today = now().date()
    target_dates = target_dates or [today, today + timedelta(days=30), today + timedelta(days=60)]
    rooms = Room.objects.all().order_by("min_age_months", "name")
    rows = []

    for room in rooms:
        points = []
        for target_date in target_dates:
            occupancy = room.occupancy(target_date)
            points.append({
                "date": target_date,
                "occupancy": occupancy,
                "capacity": room.capacity,
                "open_seats": room.capacity - occupancy,
                "percent": (occupancy / room.capacity * 100) if room.capacity else 0,
            })

        rows.append({"room": room, "points": points})

    return rows


def build_planning_overview():
    today = now().date()
    horizon = today + timedelta(days=60)

    room_rows = build_center_room_projection()
    incoming_plans = (
        MoveUpPlan.objects.select_related("child", "current_room", "target_room")
        .filter(status="planned", exit_type="moveup", target_room__isnull=False)
        .filter(planned_date__gte=today, planned_date__lte=horizon)
        .order_by("planned_date", "child__last_name")
    )
    outgoing_plans = (
        MoveUpPlan.objects.select_related("child", "current_room", "target_room")
        .filter(status="planned")
        .filter(planned_date__gte=today, planned_date__lte=horizon)
        .order_by("planned_date", "child__last_name")
    )

    incoming_by_room = defaultdict(list)
    outgoing_by_room = defaultdict(list)
    for plan in incoming_plans:
        incoming_by_room[plan.target_room_id].append(plan)
    for plan in outgoing_plans:
        outgoing_by_room[plan.current_room_id].append(plan)

    for row in room_rows:
        room_id = row["room"].id
        row["incoming"] = incoming_by_room.get(room_id, [])
        row["outgoing"] = outgoing_by_room.get(room_id, [])

    return {
        "today": today,
        "room_rows": room_rows,
        "cohorts": build_kindergarten_cohorts(),
    }
