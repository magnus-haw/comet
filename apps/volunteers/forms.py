from django import forms

from apps.people.models import Household, Parent

from .models import VolunteerEntry


class VolunteerHoursForm(forms.ModelForm):

    class Meta:

        model = VolunteerEntry

        fields = [
            "household",
            "parent",
            "service_date",
            "hours",
            "description",
        ]

        widgets = {

            "household": forms.HiddenInput(),

            "service_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),

            "hours": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.5",
                    "min": "0.5",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),

            "parent": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        household_id = kwargs.pop(
            "household_id",
            None,
        )
        
        super().__init__(*args, **kwargs)

        #
        # Prevent giant dropdowns
        #

        self.fields["household"].queryset = (
            Household.objects.filter(children__enrolled=True)
            .distinct()
        )

        self.fields["parent"].queryset = (
            Parent.objects.none()
        )
        
        self.fields["description"].help_text = (
            "Please submit ONE activity per submission. "
        )

        self.fields["service_date"].help_text = (
            "If work spanned multiple dates,"
            "submit a separate entry for each date."
        )
        #
        # If household already selected
        # populate valid parents
        #

        if self.data.get("household"):
            household_id = self.data.get("household")
            
        elif household_id is None and self.instance.pk:
            household_id = self.instance.household_id

        if household_id:

            self.fields["parent"].queryset = (
                Parent.objects
                .filter(household_id=household_id)
                .order_by("first_name")
            )

    def clean(self):

        cleaned_data = super().clean()

        household = cleaned_data.get("household")
        parent = cleaned_data.get("parent")

        #
        # Ensure parent belongs to household
        #

        if parent and household:

            if parent.household_id != household.id:

                raise forms.ValidationError(
                    "Selected parent does not belong to household."
                )

        return cleaned_data