from django.utils.timezone import now

from apps.classrooms.models import Room
from .models import Placement, MoveUpPlan
from .eligibility import child_moveup_status

from datetime import timedelta

def build_dashboard_data(room_ids=None):

    today = now().date()

    rooms_qs = Room.objects.all().order_by("min_age_months")

    if room_ids:
        rooms_qs = rooms_qs.filter(id__in=room_ids)

    rooms = list(rooms_qs)

    room_ids = [r.id for r in rooms]

    placements = (
        Placement.objects
        .select_related("child", "room")
        .filter(
            room_id__in=room_ids,
            end_date__isnull=True
        ).order_by("child__birth_date")
    )

    placements_by_room = {}

    for p in placements:
        placements_by_room.setdefault(p.room_id, []).append(p)

    child_ids = [p.child_id for p in placements]

    plans = (
        MoveUpPlan.objects
        .select_related("target_room")
        .filter(
            child_id__in=child_ids,
            status="planned"
        )
    )
    plans_by_child = {p.child_id: p for p in plans}

    plans_by_room = {}
    for p in plans:
        plans_by_room.setdefault(p.current_room_id, []).append(p)

    room_data = []

    for room in rooms:

        placements = placements_by_room.get(room.id, [])

        items = []

        for placement in placements:

            child = placement.child
            active_plan = plans_by_child.get(child.id)
            status_code, status_label = child_moveup_status(child, room)

            ready_to_implement = False

            if active_plan and active_plan.planned_date:
                ready_to_implement = (
                    active_plan.status == "planned"
                    and active_plan.planned_date <= today + timedelta(days=3)
                )

            items.append({
                "child": child,
                "status_code": status_code,
                "status_label": status_label,
                "moveup_plan": active_plan,
                "has_moveup_plan": active_plan is not None,
                "ready_to_implement": ready_to_implement,
                "today": today,
            })

        occupancy = len(items)

        room_data.append({
            "room": room,
            "children": items,
            "capacity": room.capacity,
            "occupancy": occupancy,
            "open_seats": room.capacity - occupancy,
            "upcoming_moveups": plans_by_room.get(room.id, []),
        })

    return room_data

def build_global_stats():
    rooms = Room.objects.all()
    
    placements = (
        Placement.objects
        .select_related("child__household", "room")
        .filter(end_date__isnull=True)
    )

    total_capacity = sum(r.capacity for r in rooms)
    total_children = placements.count()

    occupancy_pct = (
        (total_children / total_capacity) * 100
        if total_capacity else 0
    )

    from collections import Counter

    counts = Counter(
        p.child.household.household_type
        for p in placements
    )

    total = sum(counts.values()) or 1

    household_pct = {
        k: (v / total) * 100
        for k, v in counts.items()
    }

    return {
        "occupancy_pct": round(occupancy_pct, 1),
        "household_pct": household_pct,
        "total_children": total_children,
        "total_capacity": total_capacity,
    }


