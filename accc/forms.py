from django import forms
from .models import RoomTransition, Withdrawals

class RoomTransitionForm(forms.ModelForm):
    class Meta:
        model = RoomTransition
        fields = ['child', 'current_room', 'new_room', 'teacher_assessment', 'start_date', 
                  'sent_transition_email', 'parents_agree', 'updated_procare', 'updated_db', 
                  'updated_tuition_rate']


class WithdrawalForm(forms.ModelForm):
    class Meta:
        model = Withdrawals
        fields = ['child', 'accepted', 'room', 'teacher_assessment', 'date', 
                  'sent_email', 'parents_agree', 'updated_procare', 'updated_db', 
                  'complete']












