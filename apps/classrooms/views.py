from django.shortcuts import render
from .models import Room


def room_list(request):
    rooms = Room.objects.all().order_by("min_age_months")
    return render(request, "classrooms/room_list.html", {"rooms": rooms})
