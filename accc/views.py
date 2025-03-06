from datetime import date, timedelta
from django.utils.timezone import now

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import RoomTransition, Room, Child
from .forms import RoomTransitionForm

@login_required
def current_rooms_view(request):
    """
    Displays all rooms with their currently enrolled children, sorted by age.    """
    today = now().date()
    rooms = Room.objects.all().order_by("min_age")
    room_data = []

    for room in rooms:
        children = Child.objects.filter(room=room).order_by("birth_date")
        room.open_seats = room.capacity - children.count()
         # Add computed move-up difference
        for child in children:
            if child.expected_move_up_date:
                days_until_move_up = (child.expected_move_up_date - today).days
                
                # Assign move-up status and Bootstrap class
                if -30 <= days_until_move_up <= 30:
                    move_up_status = "Upcoming (±1 month)"
                    row_class = "table-success"
                elif -90 <= days_until_move_up < -30:
                    move_up_status = "Delayed (>1 month past)"
                    row_class = "table-warning"
                elif days_until_move_up < -90:
                    move_up_status = "Critical (>3 months past)"
                    row_class = "table-danger"
                else:
                    move_up_status = "On Schedule"
                    row_class = ""
            else:
                move_up_status = "Unknown"
                row_class = ""

            # Attach attributes to child object
            child.days_until_move_up = days_until_move_up if child.expected_move_up_date else None
            child.move_up_status = move_up_status
            child.row_class = row_class

        room_data.append({"room": room, "children": children})

    return render(request, "accc/current_rooms.html", {"room_data": room_data, "now":now().date()})

# 1. Add a Room Transition
@login_required
def add_transition(request, trans_pk=None, child_pk=None):
    """Handles adding new room transitions, editing existing ones, and pre-filling forms for specific children."""
    
    if trans_pk:
        # Editing an existing transition
        transition = get_object_or_404(RoomTransition, pk=trans_pk)
        form = RoomTransitionForm(request.POST or None, instance=transition)
        action = "Edit Transition"
    else:
        # Adding a new transition or pre-filling for a specific child
        transition = None
        initial_data = {}

        if child_pk:
            # Pre-fill child and current room if child_pk is provided
            child = get_object_or_404(Child, pk=child_pk)
            initial_data = {
                'child': child,
                'current_room': child.room
            }

        form = RoomTransitionForm(request.POST or None, initial=initial_data)
        action = "Add Transition"

    if request.method == 'POST':
        if form.is_valid():
            transition = form.save()
            if trans_pk:
                messages.success(request, f"Transition for {transition.child} updated successfully!")
            else:
                messages.success(request, f"Transition for {transition.child} added successfully!")
            return redirect('current-rooms')

    return render(request, 'accc/add_transition.html', {'form': form, 'action': action})

# 2. Send Transition Email
@require_POST
@login_required
def send_transition_email(request, transition_id):
    """Sends a transition email to parents if not already sent."""
    transition = get_object_or_404(RoomTransition, id=transition_id)
    if not transition.sent_transition_email:
        transition.send_transition_email()
        messages.success(request, f"Transition email sent to parents of {transition.child}!")
    else:
        messages.warning(request, f"Email already sent for {transition.child}.")
    return redirect('transition_detail', transition_id=transition.id)

@login_required
def delete_transition(request, trans_pk):
    """Deletes a RoomTransition object if POST request is confirmed."""
    transition = get_object_or_404(RoomTransition, pk=trans_pk)
    
    if request.method == 'POST':
        transition.delete()
        messages.success(request, f"Transition for {transition.child} has been deleted successfully!")
        return redirect('current-rooms')  # Redirect to a list view or homepage
    
    return render(request, 'accc/transition_confirm_delete.html', {'transition': transition})


# 3. Implement Transition
@require_POST
@login_required
def implement_transition(request, transition_id):
    """Marks a room transition as complete if all conditions are met."""
    transition = get_object_or_404(RoomTransition, id=transition_id)
    transition.mark_complete()
    if transition.complete:
        messages.success(request, f"Transition for {transition.child} marked as complete.")
    else:
        messages.warning(request, f"Cannot mark transition complete for {transition.child}. Check requirements.")
    return redirect('current-rooms')

# 4. Transition Detail View (to show details and action buttons)
@login_required
def transition_detail(request, transition_id):
    """Displays details of a specific room transition."""
    transition = get_object_or_404(RoomTransition, id=transition_id)
    return render(request, 'accc/transition_detail.html', {'transition': transition})

@login_required
def future_projection_view(request, year, month):
    """
    Projects what room occupancy will look like for a future date.
    Shows which children will have moved up from their current room.
    """
    target_date = date(year, month, 1)

    # Prepare data structures
    future_rooms = {room.name: {"room": room, "children": []} for room in Room.objects.all()}
    moved_children = []

    # Get all children
    children = Child.objects.all()

    for child in children:
        future_room = child.room  # Assume the child stays in the same room

        if child.expected_move_up_date and child.expected_move_up_date <= target_date:
            # Find the next room based on min_age criteria
            next_rooms = Room.objects.filter(min_age__gte=child.room.max_age).order_by("min_age")
            if next_rooms.exists():
                future_room = next_rooms.first()
                moved_children.append(child)

        if future_room:
            future_rooms[future_room.name]["children"].append(child)

    # Sort children in each room by age
    for room_name in future_rooms:
        future_rooms[room_name]["children"].sort(key=lambda c: c.birth_date)

    return render(request, "accc/future_projection.html", {
        "future_rooms": future_rooms,
        "moved_children": moved_children,
        "target_date": target_date,
    })
