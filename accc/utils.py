from datetime import date, timedelta
from collections import defaultdict
from django.db.models import Count

from .models import Child, Room, Waitlist

def get_children_moving_up(target_month):
    """
    Returns a list of children who are expected to move up in the given month.
    :param target_month: (datetime.date) The month to project for.
    :return: List of children moving up.
    """
    return Child.objects.filter(expected_move_up_date__year=target_month.year,
                                expected_move_up_date__month=target_month.month).order_by("expected_move_up_date")


def get_available_spaces_per_room(target_month):
    """
    Returns a dictionary of room names and available spaces for a given month.
    :param target_month: (datetime.date) The month to project for.
    :return: Dictionary {room_name: available_spaces}
    """
    room_spaces = {room.name: room.capacity for room in Room.objects.all()}
    children_in_rooms = Child.objects.filter(room__isnull=False)

    for child in children_in_rooms:
        # Check if the child is expected to move out before the target month
        if child.expected_move_up_date and child.expected_move_up_date < target_month:
            continue
        room_spaces[child.room.name] -= 1

    return room_spaces


def get_waitlist_priorities(target_month):
    """
    Returns a sorted list of waitlisted children who could fill available spaces.
    :param target_month: (datetime.date) The month to project for.
    :return: List of (Child, Room) tuples sorted by priority.
    """
    waitlisted_entries = Waitlist.objects.filter(date_added__lte=target_month).order_by("priority", "date_added")
    return [(entry.child, entry.room) for entry in waitlisted_entries]


def project_room_transitions(target_month):
    """
    Determines how children should transition to maximize occupancy for the target month.
    :param target_month: (datetime.date) The month to project for.
    :return: Dictionary mapping rooms to children moving in/out.
    """
    moving_up = get_children_moving_up(target_month)
    available_spaces = get_available_spaces_per_room(target_month)
    room_transitions = defaultdict(lambda: {"moving_in": [], "moving_out": []})

    for child in moving_up:
        if child.room and child.room.category in ["infant", "young_toddler", "toddler", "transitional_preschool", "early_preschool"]:
            # Find the next room for the child based on the predefined room sequence
            next_rooms = Room.objects.filter(min_age__gte=child.room.max_age).order_by("min_age")
            if next_rooms.exists():
                next_room = next_rooms.first()
                if available_spaces[next_room.name] > 0:
                    room_transitions[child.room.name]["moving_out"].append(child)
                    room_transitions[next_room.name]["moving_in"].append(child)
                    available_spaces[next_room.name] -= 1

    return room_transitions


def get_recently_enrolled_children(target_month, months_threshold=3):
    """
    Returns a list of children who have been enrolled in their current room within the past X months.
    :param target_month: (datetime.date) The month to check for.
    :param months_threshold: (int) How many months define "recently enrolled".
    :return: List of children.
    """
    threshold_date = target_month - timedelta(days=30 * months_threshold)
    return Child.objects.filter(date_enrolled_current_room__gte=threshold_date)


def optimize_class_occupancy(target_month):
    """
    Generates an occupancy projection by optimizing move-ups and filling gaps from the waitlist.
    :param target_month: (datetime.date) The month to project for.
    :return: A report showing optimized class occupancy.
    """
    room_transitions = project_room_transitions(target_month)
    waitlist = get_waitlist_priorities(target_month)
    available_spaces = get_available_spaces_per_room(target_month)
    optimized_moves = []

    # Try filling empty spaces using the waitlist
    for child, desired_room in waitlist:
        if available_spaces[desired_room.name] > 0:
            optimized_moves.append((child, desired_room))
            available_spaces[desired_room.name] -= 1

    return {
        "room_transitions": room_transitions,
        "waitlist_filled": optimized_moves,
        "final_available_spaces": available_spaces
    }
