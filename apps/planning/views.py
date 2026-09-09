from datetime import date
from django.db import transaction

from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

from apps.people.models import Child
from apps.classrooms.models import Room

from .models import Placement, MoveUpPlan
from .dashboard_logic import build_dashboard_data, build_global_stats
from .dashboard_logic import get_center_occupancy_projections
from .projections import build_planning_overview, child_planning_detail


# -------------------------------------------------------
# Utility helpers
# -------------------------------------------------------

def _require_post(request):
    if request.method != "POST":
        return HttpResponse(status=405)


def _parse_transition(target_value):
    """
    Determines transition type from form value.
    """

    if target_value == "withdrawal":
        return None, "withdrawal"

    if target_value:
        room = get_object_or_404(Room, id=target_value)
        return room, "moveup"

    return None, "moveup"


def _transition_message(request, child, exit_type, target_room=None):

    if exit_type == "moveup":
        messages.success(request, f"{child} planned move to {target_room.name}")

    elif exit_type == "withdrawal":
        messages.success(request, f"{child} planned withdraw from center.")


# -------------------------------------------------------
# Dashboard
# -------------------------------------------------------

@login_required
def dashboard(request):

    room_data = build_dashboard_data()
    stats = build_global_stats()
    occupy = get_center_occupancy_projections()

    context = {
        "room_data": room_data,
        "global_stats": stats,
        "today": now().date(),
        "occupancy_projection":occupy, 
    }

    return render(
        request,
        "planning/dashboard.html",
        context
    )


@login_required
def planning_overview(request):
    return render(
        request,
        "planning/overview.html",
        build_planning_overview(),
    )


@login_required
def child_planning(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    return render(
        request,
        "planning/child_detail.html",
        child_planning_detail(child),
    )

# -------------------------------------------------------
# Transition form (create)
# -------------------------------------------------------
@login_required
def moveup_form(request, child_id):

    child = get_object_or_404(Child, id=child_id)

    room_id = request.GET.get("room_id")
    current_room = get_object_or_404(Room, id=room_id)

    today = date.today()

    age_months = (
        (today.year - child.birth_date.year) * 12
        + (today.month - child.birth_date.month)
    )

    rooms = Room.objects.filter(
        min_age_months__lte=age_months + 3,
        max_age_months__gte=age_months - 1,
    ).exclude(id=current_room.id).order_by("min_age_months")

    max_room = Room.objects.order_by("-max_age_months").first()

    return render(
        request,
        "planning/partials/transition_form.html",
        {
            "child": child,
            "rooms": rooms,
            "current_room": current_room,
            "today": today,
        },
    )


# -------------------------------------------------------
# Create transition
# -------------------------------------------------------
@login_required
def create_moveup(request):

    resp = _require_post(request)
    if resp:
        return resp

    child = get_object_or_404(Child, id=request.POST.get("child_id"))
    current_room = get_object_or_404(Room, id=request.POST.get("room_id"))

    target_room, exit_type = _parse_transition(
        request.POST.get("target_room")
    )

    planned_date = request.POST.get("planned_date")
    notes = request.POST.get("teacher_notes")

    # validation: active placement
    placement = Placement.objects.filter(
        child=child,
        room=current_room,
        end_date__isnull=True,
    ).first()

    if not placement:
        messages.error(request, "Child not assigned to this room.")
        return _refresh_room_card(request, current_room)

    # prevent duplicate plan
    if MoveUpPlan.objects.filter(
        child=child,
        status__in=["draft", "planned"]
    ).exists():

        messages.error(request, "Active move-up plan already exists.")
        return _refresh_room_card(request, current_room)

    # prevent same-room move
    if target_room and target_room.id == current_room.id:
        messages.error(request, "Target room must be different.")
        return _refresh_room_card(request, current_room)

    MoveUpPlan.objects.create(
        child=child,
        current_room=current_room,
        target_room=target_room,
        planned_date=planned_date,
        teacher_notes=notes,
        exit_type=exit_type,
        status="planned",
    )

    _transition_message(request, child, exit_type, target_room)

    return _refresh_room_card(request, current_room)


# -------------------------------------------------------
# Edit form
# -------------------------------------------------------
@login_required
def edit_moveup_form(request, plan_id):

    plan = get_object_or_404(MoveUpPlan, id=plan_id)

    current_room = plan.current_room

    today = date.today()

    age_months = (
        (today.year - plan.child.birth_date.year) * 12
        + (today.month - plan.child.birth_date.month)
    )

    rooms = Room.objects.filter(
        min_age_months__lte=age_months + 3,
        max_age_months__gte=age_months - 1,
    ).exclude(id=current_room.id).order_by("min_age_months")
    
    max_room = Room.objects.order_by("-max_age_months").first()

    return render(
        request,
        "planning/partials/transition_form.html",
        {
            "plan": plan,
            "rooms": rooms,
            "current_room": current_room,
            "today": date.today(),
        },
    )


# -------------------------------------------------------
# Update transition
# -------------------------------------------------------
@login_required
def update_moveup(request, plan_id):

    resp = _require_post(request)
    if resp:
        return resp

    plan = get_object_or_404(MoveUpPlan, id=plan_id)

    target_room, exit_type = _parse_transition(
        request.POST.get("target_room")
    )

    if target_room and target_room.id == plan.current_room.id:
        messages.error(request, "Target room must be different.")
        return _refresh_room_card(request, plan.current_room)

    plan.target_room = target_room
    plan.exit_type = exit_type
    plan.planned_date = request.POST.get("planned_date")
    plan.teacher_notes = request.POST.get("teacher_notes")

    plan.save()

    _transition_message(request, plan.child, exit_type, target_room)

    return _refresh_room_card(request, plan.current_room)


# -------------------------------------------------------
# Cancel transition
# -------------------------------------------------------
@login_required
def cancel_moveup(request, plan_id):

    resp = _require_post(request)
    if resp:
        return resp

    plan = get_object_or_404(MoveUpPlan, id=plan_id)

    plan.status = "cancelled"
    plan.save()

    messages.warning(request, "Move-up plan cancelled.")

    return _refresh_room_card(request, plan.current_room)


# -------------------------------------------------------
# Implement transition
# -------------------------------------------------------
@login_required
def implement_moveup(request, plan_id):

    resp = _require_post(request)
    if resp:
        return resp

    plan = get_object_or_404(MoveUpPlan, id=plan_id)

    child = plan.child
    source_room = plan.current_room
    target_room = plan.target_room

    placement = Placement.objects.filter(
        child=child,
        room=source_room,
        end_date__isnull=True,
    ).first()

    effective_date = plan.planned_date
    if effective_date is None:
        messages.error(request, "Set an effective date before implementing this transition.")
        return _refresh_room_card(request, source_room)

    if placement and effective_date < placement.start_date:
        messages.error(
            request,
            "The effective date cannot be before the child's current placement start date.",
        )
        return _refresh_room_card(request, source_room)

    with transaction.atomic():
        if placement:
            placement.end_date = effective_date
            placement.save(update_fields=["end_date"])

        if plan.exit_type == "moveup":
            Placement.objects.create(
                child=child,
                room=target_room,
                start_date=effective_date,
            )
        else:
            child.enrolled = False
            child.save(update_fields=["enrolled"])

        plan.status = "completed"
        plan.save(update_fields=["status"])

    _transition_message(request, child, plan.exit_type, target_room)

    if plan.exit_type == "moveup":
        return _refresh_two_room_cards(request, source_room, target_room)

    return _refresh_room_card(request, source_room)


# -------------------------------------------------------
# HTMX refresh helpers
# -------------------------------------------------------
def _refresh_room_card(request, room):

    data = build_dashboard_data(room_ids=[room.id])[0]

    room_html = render_to_string(
        "planning/partials/room_card.html",
        {"data": data},
        request=request,
    )

    messages_html = render_to_string(
        "partials/messages.html",
        {},
        request=request,
    )

    return HttpResponse(
        room_html +
        f"""
        <div id="messages-container" hx-swap-oob="innerHTML">
            {messages_html}
        </div>
        """
    )

def _refresh_two_room_cards(request, room_a, room_b):

    rooms = build_dashboard_data(room_ids=[room_a.id, room_b.id])

    room_map = {r["room"].id: r for r in rooms}

    room_a_html = render_to_string(
        "planning/partials/room_card.html",
        {"data": room_map[room_a.id]},
        request=request,
    )

    room_b_html = render_to_string(
        "planning/partials/room_card.html",
        {"data": room_map[room_b.id]},
        request=request,
    )

    messages_html = render_to_string(
        "partials/messages.html",
        {},
        request=request,
    )

    return HttpResponse(
        f"""
        {room_a_html}

        <div id="room-card-{room_b.id}" hx-swap-oob="outerHTML">
            {room_b_html}
        </div>

        <div id="messages-container" hx-swap-oob="innerHTML">
            {messages_html}
        </div>
        """
    )
















