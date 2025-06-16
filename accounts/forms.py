# accounts/forms.py

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile

from django import forms
ROLE_CHOICES = [
    ('public', 'Public User'),
    ('officer', 'Environmental Officer'),
    ('admin', 'Administrator'),
]


class RegisterForm(forms.Form):
    email = forms.EmailField(
        label='Email', 
        max_length=100,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Email Address',
            'id': 'inputEmail'
        })
    )
    password1 = forms.CharField(
        label='Password', 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Password',
            'id': 'inputPassword'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password', 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Confirm Password',
            'id': 'inputConfirmPassword'
        })
    )
    role = forms.ChoiceField(
        label='Account Type',
        choices=ROLE_CHOICES,
        initial='public',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'inputRole'
        }),
        help_text='Select the type of account you need.'
    )
    location = forms.ChoiceField(
        label='Location',
        choices=UserProfile.NAIROBI_CONSTITUENCIES,
        initial='other',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'inputLocation'
        }),
        help_text='Select your constituency.'
    )

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get('password1')
        pw2 = cleaned_data.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Email Address',
            'id': 'inputEmail'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Password',
            'id': 'inputPassword'
        })
    )