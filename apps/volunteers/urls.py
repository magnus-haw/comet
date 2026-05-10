from django.urls import path

from .views import (
    VolunteerOpportunityListView,
    VolunteerHoursCreateView,
    HouseholdSearchView,
    HouseholdParentOptionsView,
    HouseholdSummaryView,
    VolunteerHoursDeleteView,
)

app_name = "volunteers"

urlpatterns = [

    path(
        "",
        VolunteerOpportunityListView.as_view(),
        name="opportunity_list",
    ),

    path(
        "submit/",
        VolunteerHoursCreateView.as_view(),
        name="hours_submit",
    ),

    path(
        "household-search/",
        HouseholdSearchView.as_view(),
        name="household_search",
    ),

    path(
        "households/<int:household_id>/parents/",
        HouseholdParentOptionsView.as_view(),
        name="household_parents",
    ),
    
    path(
        "households/<int:household_id>/",
        HouseholdSummaryView.as_view(),
        name="household_summary",
    ),
    
    path(
        "hours/<int:pk>/delete/",
        VolunteerHoursDeleteView.as_view(),
        name="hours_delete",
    ),
]