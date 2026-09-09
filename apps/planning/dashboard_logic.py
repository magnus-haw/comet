from datetime import timedelta
from collections import Counter, defaultdict

from django.db.models import Q
from django.utils.timezone import now

from apps.classrooms.models import Room
from .models import Placement, MoveUpPlan
from .eligibility import child_moveup_status


def _active_placements(target_date, room_ids=None):
    qs = Placement.objects.select_related("child", "child__household", "room").filter(
        start_date__lte=target_date,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gt=target_date))
    if room_ids:
        qs = qs.filter(room_id__in=room_ids)
    return qs


def build_dashboard_data(room_ids=None):
    today = now().date()
    horizon = today + timedelta(days=60)

    rooms_qs = Room.objects.all().order_by("min_age_months", "name")
    if room_ids:
        rooms_qs = rooms_qs.filter(id__in=room_ids)
    rooms = list(rooms_qs)
    ids = [r.id for r in rooms]

    placements = _active_placements(today, ids).order_by("child__birth_date")
    placements_by_room = defaultdict(list)
    for placement in placements:
        placements_by_room[placement.room_id].append(placement)

    child_ids = [p.child_id for p in placements]
    plans = (
        MoveUpPlan.objects.select_related("child", "current_room", "target_room")
        .filter(child_id__in=child_ids, status="planned")
    )
    plans_by_child = {p.child_id: p for p in plans}

    planned_incoming = (
        MoveUpPlan.objects.select_related("child", "current_room", "target_room")
        .filter(status="planned", exit_type="moveup", target_room_id__in=ids)
        .filter(planned_date__gte=today, planned_date__lte=horizon)
        .order_by("planned_date")
    )
    planned_outgoing = (
        MoveUpPlan.objects.select_related("child", "current_room", "target_room")
        .filter(status="planned", current_room_id__in=ids)
        .filter(planned_date__gte=today, planned_date__lte=horizon)
        .order_by("planned_date")
    )
    incoming_by_room = defaultdict(list)
    outgoing_by_room = defaultdict(list)
    for plan in planned_incoming:
        incoming_by_room[plan.target_room_id].append(plan)
    for plan in planned_outgoing:
        outgoing_by_room[plan.current_room_id].append(plan)

    # Future placements capture already-implemented future enrollments/moves.
    future_placements = (
        Placement.objects.select_related("child", "room")
        .filter(room_id__in=ids, start_date__gt=today, start_date__lte=horizon)
        .order_by("start_date")
    )
    future_by_room = defaultdict(list)
    for placement in future_placements:
        future_by_room[placement.room_id].append(placement)

    room_data = []
    for room in rooms:
        items = []
        for placement in placements_by_room.get(room.id, []):
            child = placement.child
            active_plan = plans_by_child.get(child.id)
            status_code, status_label = child_moveup_status(child, room)
            ready_to_implement = bool(
                active_plan
                and active_plan.planned_date
                and active_plan.status == "planned"
                and active_plan.planned_date <= today + timedelta(days=3)
            )
            items.append({
                "child": child,
                "placement": placement,
                "status_code": status_code,
                "status_label": status_label,
                "moveup_plan": active_plan,
                "has_moveup_plan": active_plan is not None,
                "ready_to_implement": ready_to_implement,
                "today": today,
            })

        projections = []
        for label, target_date in [
            ("Today", today),
            ("+30", today + timedelta(days=30)),
            ("+60", today + timedelta(days=60)),
        ]:
            occupancy = room.occupancy(target_date)
            projections.append({
                "label": label,
                "date": target_date,
                "occupancy": occupancy,
                "capacity": room.capacity,
                "open_seats": room.capacity - occupancy,
            })

        room_data.append({
            "room": room,
            "children": items,
            "capacity": room.capacity,
            "occupancy": len(items),
            "open_seats": room.capacity - len(items),
            "projections": projections,
            "incoming_plans": incoming_by_room.get(room.id, []),
            "future_placements": future_by_room.get(room.id, []),
            "outgoing_plans": outgoing_by_room.get(room.id, []),
        })

    return room_data


def build_global_stats():
    today = now().date()
    rooms = Room.objects.all()
    placements = _active_placements(today)

    total_capacity = sum(r.capacity for r in rooms)
    total_children = placements.count()
    occupancy_pct = (total_children / total_capacity * 100) if total_capacity else 0

    counts = Counter(p.child.household.household_type for p in placements)
    total = sum(counts.values()) or 1
    household_pct = {k: (v / total) * 100 for k, v in counts.items()}

    return {
        "occupancy_pct": round(occupancy_pct, 1),
        "household_pct": household_pct,
        "total_children": total_children,
        "total_capacity": total_capacity,
    }


def get_center_occupancy_projections():
    today = now().date()
    rooms = list(Room.objects.all())

    def compute(target_date):
        total_children = sum(r.occupancy(target_date) for r in rooms)
        total_capacity = sum(r.capacity for r in rooms)
        return {
            "date": target_date,
            "children": total_children,
            "capacity": total_capacity,
            "percent": (total_children / total_capacity) * 100 if total_capacity else 0,
        }

    return {
        "today": compute(today),
        "plus_30": compute(today + timedelta(days=30)),
        "plus_60": compute(today + timedelta(days=60)),
    }
