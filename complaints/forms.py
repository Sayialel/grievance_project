from django import forms
from datetime import date, timedelta
from .models import Complaint, ComplaintActivity, ComplaintStatus, ComplaintCategory
from accounts.models import UserProfile

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'location', 'category', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Issue Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Detailed Description'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'})
        }

class ComplaintActivityForm(forms.ModelForm):
    class Meta:
        model = ComplaintActivity
        fields = ['note', 'attached_file']
        widgets = {
            'note': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Add your notes about this complaint...', 'rows': 3}),
            'attached_file': forms.FileInput(attrs={'class': 'form-control'})
        }

class ComplaintStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'})
        }

class ComplaintFilterForm(forms.Form):
    SORT_CHOICES = [
        ('location', 'Location (A-Z)'),
        ('-location', 'Location (Z-A)'),
        ('-date_submitted', 'Newest First'),
        ('date_submitted', 'Oldest First'),
    ]

    status = forms.MultipleChoiceField(
        required=False,
        choices=ComplaintStatus.choices,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    category = forms.MultipleChoiceField(
        required=False,
        choices=ComplaintCategory.choices,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    location = forms.MultipleChoiceField(
        required=False,
        choices=UserProfile.NAIROBI_CONSTITUENCIES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    reported_by = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'User Email'})
    )

    sort_by = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='-date_submitted',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize date range to last 30 days by default if no date is provided
        if not args and not kwargs.get('data'):
            today = date.today()
            thirty_days_ago = today - timedelta(days=30)
            self.initial['date_from'] = thirty_days_ago
            self.initial['date_to'] = today

class OfficerReassignForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['assigned_officer']

    def __init__(self, *args, **kwargs):
        complaint_location = kwargs.pop('complaint_location', None)
        super().__init__(*args, **kwargs)

        if complaint_location:
            # Filter officers by the complaint's location
            officers = UserProfile.objects.filter(role='officer', location=complaint_location)
            self.fields['assigned_officer'].queryset = officers
            self.fields['assigned_officer'].widget.attrs.update({'class': 'form-select'})
