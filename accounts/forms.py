# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'phone_number', 'password1', 'password2', 'profile_image']

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Username or Email')
