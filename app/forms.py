from django import forms
from .models import Profile, Module, Question, Sem

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['sem', 'year']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make fields required
        self.fields['sem'].required = True
        self.fields['year'].required = True

        # Remove empty choice from dropdowns
        self.fields['sem'].empty_label = None
        self.fields['year'].empty_label = None