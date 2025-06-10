# complaints/forms.py

from django import forms
from .models import Complaint, ComplaintStatus


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'location', 'category', 'image']


class StatusUpdateForm(forms.ModelForm):
    status = forms.ChoiceField(choices=ComplaintStatus.choices)

    class Meta:
        model = Complaint
        fields = ['status']
# complaints/forms.py

from django import forms
from .models import Complaint, ComplaintStatus


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'location', 'category', 'image']


class StatusUpdateForm(forms.ModelForm):
    status = forms.ChoiceField(choices=ComplaintStatus.choices)

    class Meta:
        model = Complaint
        fields = ['status']
