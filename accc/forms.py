from django import forms
from .models import RoomTransition

class RoomTransitionForm(forms.ModelForm):
    class Meta:
        model = RoomTransition
        fields = ['child', 'current_room', 'new_room', 'teacher_assessment', 'start_date', 
                  'sent_transition_email', 'parents_agree', 'updated_procare', 'updated_db', 
                  'updated_tuition_rate']
