from datetime import date

from django.db.models import Q
from django.shortcuts import render
from django.views import View
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.views.generic import DeleteView

from apps.people.models import Household, Parent

from .forms import VolunteerHoursForm
from .models import VolunteerEntry, VolunteerOpportunity
from .services import required_household_hours

class VolunteerOpportunityListView(ListView):
    model = VolunteerOpportunity
    template_name = "volunteers/opportunity_list.html"
    context_object_name = "opportunities"

    def get_queryset(self):
        return (
            VolunteerOpportunity.objects
            .filter(is_active=True)
            .order_by("event_date", "title")
        )


class VolunteerHoursCreateView(CreateView):

    model = VolunteerEntry

    form_class = VolunteerHoursForm

    template_name = "volunteers/hours_form.html"

    # def get_initial(self):

    #     initial = super().get_initial()

    #     household_id = self.request.GET.get("household")

    #     if household_id:

    #         initial["household"] = household_id

    #     return initial

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()

        household_id = (
            self.request.GET.get("household")
            or self.request.POST.get("household")
        )

        kwargs["household_id"] = household_id

        return kwargs
    
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        household = None

        household_label = ""

        household_id = (
            self.request.GET.get("household")
            or self.request.POST.get("household")
        )

        if household_id:

            try:

                household = (
                    Household.objects
                    .prefetch_related("children")
                    .get(pk=household_id)
                )

                child_names = ", ".join(
                    child.first_name
                    for child in household.children.filter(
                        enrolled=True
                    )
                )

                household_label = (
                    f"{household.name} ({child_names})"
                )

            except Household.DoesNotExist:

                pass

        context["selected_household"] = household

        context["household_label"] = household_label

        return context
    
    def get_success_url(self):

        return reverse_lazy(
            "volunteers:household_summary",
            kwargs={
                "household_id": self.object.household_id,
            },
        )

class VolunteerHoursDeleteView(DeleteView):

    model = VolunteerEntry

    template_name = "volunteers/hours_confirm_delete.html"

    context_object_name = "submission"

    def get_queryset(self):

        #
        # Only allow deletion of pending entries
        #

        return (
            VolunteerEntry.objects
            .filter(status="pending")
        )

    def get_success_url(self):

        return reverse_lazy(
            "volunteers:household_summary",
            kwargs={
                "household_id": self.object.household_id,
            },
        )

class HouseholdSearchView(View):

    template_name = "partials/household_results.html"

    def get(self, request):

        q = request.GET.get("q", "").strip()

        households = Household.objects.none()

        if len(q) >= 2:

            households = (
                Household.objects
                .prefetch_related("children", "parents")
                .filter(children__enrolled=True)
                .filter(
                    Q(name__icontains=q)
                    |
                    Q(parents__first_name__icontains=q)
                    |
                    Q(parents__last_name__icontains=q)
                    |
                    Q(children__first_name__icontains=q)
                    |
                    Q(children__last_name__icontains=q)
                )
                .distinct()[:10]
            )

        return render(
            request,
            self.template_name,
            {
                "households": households,
            },
        )

class HouseholdParentOptionsView(View):

    template_name = "partials/parent_options.html"

    def get(self, request, household_id):

        parents = (
            Parent.objects
            .filter(household_id=household_id)
            .order_by("first_name")
        )

        return render(
            request,
            self.template_name,
            {
                "parents": parents,
            },
        )

class HouseholdSummaryView(TemplateView):

    template_name = "volunteers/household_summary.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
    
        household = get_object_or_404(
            Household,
            pk=self.kwargs["household_id"],
        )

        submissions = (
            VolunteerEntry.objects
            .filter(household=household)
            .select_related(
                "parent",
            )
            .order_by("-service_date")
        )

        #
        # Approved hours
        #

        approved_hours = (
            submissions
            .filter(status="approved")
            .aggregate(total=Sum("hours"))
            ["total"]
            or 0
        )

        #
        # Pending hours
        #

        pending_hours = (
            submissions
            .filter(status="pending")
            .aggregate(total=Sum("hours"))
            ["total"]
            or 0
        )

        #
        # Required hours
        #


        today = date.today()

        #
        # PPP year starts June 1
        #

        if today.month >= 6:

            ppp_year = today.year

        else:

            ppp_year = today.year - 1

        required_hours = required_household_hours(
            household,
            ppp_year,
        )

        remaining_hours = max(
            required_hours - approved_hours,
            0,
        )

        context.update({

            "household": household,

            "submissions": submissions,

            "approved_hours": approved_hours,

            "pending_hours": pending_hours,

            "required_hours": required_hours,

            "remaining_hours": remaining_hours,
            "ppp_year" : ppp_year,
        })

        return context





