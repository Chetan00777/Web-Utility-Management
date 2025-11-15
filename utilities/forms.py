from django import forms
from .models import Utility

class UtilityForm(forms.ModelForm):
    file = forms.FileField(required=False, label='Utility File (optional)')

    class Meta:
        model = Utility
        fields = ['type', 'usage', 'date', 'notes', 'file']
