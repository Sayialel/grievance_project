import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import UserProfile
from utils.firebase import db
from firebase_admin import firestore
from os import environ

# Get API key from environment variables
FIREBASE_API_KEY = environ.get('FIREBASE_API_KEY')

# ---------------------------
# Register View
# ---------------------------
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')  # ensure form has password1
            role = form.cleaned_data.get('role')  # Get selected role from form

            payload = {
                'email': email,
                'password': password,
                'returnSecureToken': True
            }
            firebase_url = f'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}'

            response = requests.post(firebase_url, json=payload)
            data = response.json()

            if 'idToken' in data:
                # Get the UID from Firebase response
                uid = data['localId']

                # Create UserProfile in Django model
                location = form.cleaned_data.get('location', 'other')
                # Ensure location is required for officers
                if role == 'officer' and location == 'other':
                    messages.error(request, 'Environmental Officers must select a specific constituency.')
                    return render(request, 'accounts/register.html', {'form': form})

                user_profile = UserProfile.objects.create(
                    uid=uid,
                    email=email,
                    role=role,
                    location=location
                )

                # Save user data to Firestore
                db.collection('users').document(uid).set({
                    'email': email,
                    'role': role,
                    'location': location,
                    'created_at': firestore.SERVER_TIMESTAMP
                })

                messages.success(request, 'Account created successfully. Please log in.')
                return redirect('accounts:login')
            else:
                error = data.get('error', {}).get('message', 'Registration failed.')
                messages.error(request, f"Firebase Error: {error}")
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

# ---------------------------
# Login View
# ---------------------------
def login_view(request):

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            payload = {
                'email': email,
                'password': password,
                'returnSecureToken': True
            }

            firebase_url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}'

            response = requests.post(firebase_url, json=payload)
            data = response.json()

            if 'idToken' in data:
                uid = data['localId']
                email = data['email']

                # Save Firebase data to session
                request.session['firebase_id_token'] = data['idToken']
                request.session['firebase_local_id'] = uid
                request.session['firebase_email'] = email

                # ✅ Get or create UserProfile in Django
                user_profile, created = UserProfile.objects.get_or_create(
                    uid=uid,
                    defaults={
                        'email': email,
                        'role': 'public'  # default role
                    }
                )

                # Store the user's role in the session
                request.session['user_role'] = user_profile.role

                request.session['firebase_user'] = {
                    'uid': uid,
                    'email': email,
                    'role': user_profile.role
                }

                # Check if user exists in Firestore
                user_doc = db.collection('users').document(uid).get()
                if not user_doc.exists:
                    # If user doesn't exist in Firestore, create it
                    db.collection('users').document(uid).set({
                        'email': email,
                        'role': user_profile.role,
                        'created_at': firestore.SERVER_TIMESTAMP
                    })

                messages.success(request, 'Login successful.')

                # Check if there's a next URL to redirect to
                next_url = request.session.get('next')
                if next_url:
                    del request.session['next']
                    return redirect(next_url)

                # Otherwise redirect based on user role
                if user_profile.role == 'officer':
                    return redirect('dashboard:officer_dashboard')
                elif user_profile.role == 'admin':
                    return redirect('dashboard:admin_dashboard')
                else:  # public user
                    return redirect('complaints:user_dashboard')
            else:
                error = data.get('error', {}).get('message', 'Login failed.')
                messages.error(request, f"Firebase Error: {error}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()

        # Store next parameter if provided in the URL
        next_param = request.GET.get('next')
        if next_param:
            request.session['next'] = next_param

    return render(request, 'accounts/login.html', {'form': form})



# ---------------------------
# Logout View
# ---------------------------
def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('home')

# ---------------------------
# Profile View
# ---------------------------
def profile_view(request):
    uid = request.session.get('firebase_local_id')
    email = request.session.get('firebase_email')

    if not uid:
        messages.error(request, 'You must be logged in to view your profile.')
        return redirect('accounts:login')

    profile = UserProfile.objects.filter(uid=uid).first()

    context = {
        'email': email,
        'uid': uid,
        'role': profile.role if profile else 'Unknown'
    }

    return render(request, 'accounts/profile.html', context)

