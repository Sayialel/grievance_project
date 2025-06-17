from django.contrib import messages
from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone

from accounts.models import UserProfile
from .models import Complaint, ComplaintActivity, ComplaintStatus
from .forms import (
    ComplaintForm, ComplaintActivityForm, ComplaintStatusUpdateForm, 
    ComplaintFilterForm, OfficerReassignForm
)
from .decorators import admin_required, officer_required
from .utils import auto_assign_officer

def homepage(request):
    return render(request, 'complaints/homepage.html')

def dashboard_view(request):
    """Redirects users to the appropriate dashboard based on their role"""
    # Check if user is logged in via Firebase
    uid = request.session.get('firebase_local_id')
    if not uid:
        messages.error(request, 'You must be logged in to access the dashboard.')
        # Store the intended URL for redirection after login
        request.session['next'] = request.path
        return redirect('accounts:login')

    # Get user role from session
    user_role = request.session.get('user_role')

    # Redirect based on role
    if user_role == 'admin':
        return redirect('dashboard:admin_dashboard')
    elif user_role == 'officer':
        return redirect('dashboard:officer_dashboard')
    else:  # public user
        return redirect('complaints:user_dashboard')

def submit_complaint(request):
    # Check if user is logged in via Firebase
    uid = request.session.get('firebase_local_id')
    if not uid:
        messages.error(request, 'You must be logged in to submit a complaint.')
        return redirect('accounts:login')

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Create complaint but don't save yet
            complaint = form.save(commit=False)
            # Get user from UserProfile using Firebase UID
            user_profile = UserProfile.objects.get(uid=uid)
            complaint.user = user_profile
            complaint.save()

            # Auto assign an officer
            assigned_officer = auto_assign_officer(complaint)

            # Save complaint to Firebase
            from utils.firebase import db
            from firebase_admin import firestore

            # Create complaint data for Firebase
            complaint_data = {
                'id': complaint.id,
                'title': complaint.title,
                'description': complaint.description,
                'location': complaint.location,
                'location_display': complaint.get_location_display(),
                'category': complaint.category,
                'status': complaint.status,
                'date_submitted': firestore.SERVER_TIMESTAMP,
                'user_uid': uid,
                'user_email': user_profile.email,
                'has_image': bool(complaint.image),
                'assigned_officer': assigned_officer.email if assigned_officer else None
            }

            # Add to Firebase complaints collection
            db.collection('complaints').document(str(complaint.id)).set(complaint_data)

            # Create initial activity record
            activity_data = {
                'complaint_id': complaint.id,
                'officer_uid': None,
                'officer_email': None,
                'note': "Complaint submitted by user",
                'created_at': firestore.SERVER_TIMESTAMP,
                'status': complaint.status,
                'activity_type': 'complaint_creation',
                'has_attachment': bool(complaint.image)
            }

            # Add to Firebase activities collection
            db.collection('complaint_activities').add(activity_data)

            if assigned_officer:
                messages.success(request, f"Your complaint has been submitted and assigned to an officer in {complaint.get_location_display()}.")
            else:
                messages.success(request, "Your complaint has been submitted. An officer will be assigned soon.")

            return redirect('complaints:complaint_success')
    else:
        form = ComplaintForm()

    return render(request, 'complaints/submit_complaint.html', {'form': form})

def complaint_success(request):
    # Check if user is logged in via Firebase
    uid = request.session.get('firebase_local_id')
    if not uid:
        messages.error(request, 'You must be logged in to view this page.')
        return redirect('accounts:login')

    return render(request, 'complaints/complaint_success.html')

def user_dashboard(request):
    """Dashboard for public users to submit and view their complaints"""
    # Check if user is logged in via Firebase
    uid = request.session.get('firebase_local_id')
    if not uid:
        messages.error(request, 'You must be logged in to view your dashboard.')
        return redirect('accounts:login')

    # Get user profile
    user_profile = UserProfile.objects.get(uid=uid)

    # Handle complaint submission
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Create complaint but don't save yet
            complaint = form.save(commit=False)
            complaint.user = user_profile
            complaint.save()

            # Auto assign an officer
            assigned_officer = auto_assign_officer(complaint)

            if assigned_officer:
                messages.success(request, f"Your complaint has been submitted and assigned to an officer in {complaint.get_location_display()}.")
            else:
                messages.success(request, "Your complaint has been submitted. An officer will be assigned soon.")

            # Redirect to the same page to avoid form resubmission
            return redirect('complaints:user_dashboard')
    else:
        form = ComplaintForm()

    # Get complaints for this user (simple list without filtering)
    user_complaints = Complaint.objects.filter(user=user_profile).order_by('-date_submitted')

    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(user_complaints, 10)  # 10 complaints per page
    page = request.GET.get('page')
    try:
        complaints = paginator.page(page)
    except PageNotAnInteger:
        complaints = paginator.page(1)
    except EmptyPage:
        complaints = paginator.page(paginator.num_pages)

    context = {
        'complaints': complaints,
        'form': form,  # Add the form for complaint submission
        'user_type': 'public',
        'user_email': user_profile.email
    }
    return render(request, 'complaints/user_dashboard.html', context)

def officer_dashboard(request):
    """Dashboard for officers to view complaints assigned to them"""
    # Check if user is logged in via Firebase
    uid = request.session.get('firebase_local_id')
    user_role = request.session.get('user_role')

    if not uid or user_role != 'officer':
        messages.error(request, 'You must be logged in as an Environmental Officer to access this page.')
        return redirect('accounts:login')

    # Get user profile
    officer = UserProfile.objects.filter(uid=uid).first()
    if not officer:
        messages.error(request, 'Officer profile not found.')
        return redirect('accounts:login')

    # Get complaints assigned to this officer
    officer_complaints = Complaint.objects.filter(assigned_officer=officer).order_by('-date_submitted')

    # Filtering
    filter_form = ComplaintFilterForm(request.GET or None)
    if filter_form.is_valid():
        # Apply filters
        filters = {}
        if filter_form.cleaned_data.get('status'):
            filters['status__in'] = filter_form.cleaned_data['status']
        if filter_form.cleaned_data.get('category'):
            filters['category__in'] = filter_form.cleaned_data['category']
        if filter_form.cleaned_data.get('date_from'):
            filters['date_submitted__gte'] = filter_form.cleaned_data['date_from']
        if filter_form.cleaned_data.get('date_to'):
            filters['date_submitted__lte'] = filter_form.cleaned_data['date_to']

        if filters:
            officer_complaints = officer_complaints.filter(**filters)

        # Apply sorting
        sort_by = filter_form.cleaned_data.get('sort_by')
        if sort_by:
            officer_complaints = officer_complaints.order_by(sort_by)

    # Pagination
    paginator = Paginator(officer_complaints, 10)  # 10 complaints per page
    page = request.GET.get('page')
    try:
        complaints = paginator.page(page)
    except PageNotAnInteger:
        complaints = paginator.page(1)
    except EmptyPage:
        complaints = paginator.page(paginator.num_pages)

    context = {
        'complaints': complaints,
        'filter_form': filter_form,
        'user_type': 'officer',
        'email': request.session.get('firebase_email')
    }
    return render(request, 'complaints/complaint_list.html', context)

def admin_dashboard(request):
    """Dashboard for admins to view all complaints"""
    # Check if user is logged in via Firebase
    uid = request.session.get('firebase_local_id')
    user_role = request.session.get('user_role')

    if not uid or user_role != 'admin':
        messages.error(request, 'You must be logged in as an Administrator to access this page.')
        return redirect('accounts:login')

    # Get all complaints
    all_complaints = Complaint.objects.all().order_by('-date_submitted')

    # Filtering
    filter_form = ComplaintFilterForm(request.GET or None)
    if filter_form.is_valid():
        # Apply filters
        filters = {}
        if filter_form.cleaned_data.get('status'):
            filters['status__in'] = filter_form.cleaned_data['status']
        if filter_form.cleaned_data.get('category'):
            filters['category__in'] = filter_form.cleaned_data['category']
        if filter_form.cleaned_data.get('location'):
            filters['location__in'] = filter_form.cleaned_data['location']
        if filter_form.cleaned_data.get('date_from'):
            filters['date_submitted__gte'] = filter_form.cleaned_data['date_from']
        if filter_form.cleaned_data.get('date_to'):
            filters['date_submitted__lte'] = filter_form.cleaned_data['date_to']

        # Filter by reported user
        if filter_form.cleaned_data.get('reported_by'):
            email = filter_form.cleaned_data['reported_by']
            filters['user__email__icontains'] = email

        if filters:
            all_complaints = all_complaints.filter(**filters)

        # Apply sorting
        sort_by = filter_form.cleaned_data.get('sort_by')
        if sort_by:
            all_complaints = all_complaints.order_by(sort_by)

    # Pagination
    paginator = Paginator(all_complaints, 10)  # 10 complaints per page
    page = request.GET.get('page')
    try:
        complaints = paginator.page(page)
    except PageNotAnInteger:
        complaints = paginator.page(1)
    except EmptyPage:
        complaints = paginator.page(paginator.num_pages)

    context = {
        'complaints': complaints,
        'filter_form': filter_form,
        'user_type': 'admin',
        'email': request.session.get('firebase_email')
    }
    return render(request, 'complaints/complaint_list.html', context)

def complaint_detail(request, pk=None, complaint_id=None):
    """View for displaying complaint details and handling updates"""
    # Use whichever id is provided
    complaint_id = pk or complaint_id
    complaint = get_object_or_404(Complaint, pk=complaint_id)

    # Check if user is logged in via Firebase
    uid = request.session.get('firebase_local_id')
    if not uid:
        messages.error(request, 'You must be logged in to view complaint details.')
        # Store the intended URL for redirection after login
        request.session['next'] = request.path
        return redirect('accounts:login')

    # Get user profile and role
    user_profile = UserProfile.objects.filter(uid=uid).first()
    if not user_profile:
        messages.error(request, 'User profile not found.')
        return redirect('accounts:login')

    user_role = request.session.get('user_role')

    # Check permissions
    if user_role == 'public' and complaint.user != user_profile:
        messages.error(request, "You don't have permission to view this complaint.")
        return redirect('complaints:user_dashboard')
    elif user_role == 'officer' and complaint.assigned_officer != user_profile:
        # For officers, check if the complaint is in their area
        if complaint.location != user_profile.location:
            messages.error(request, "This complaint is not in your assigned area.")
            return redirect('dashboard:officer_dashboard')

    # Get activities from Django database
    django_activities = complaint.activities.all().order_by('-created_at')

    # Also get activities from Firebase for comparison (using both sources during transition)
    firebase_activities = []
    try:
        from utils.firebase_sync import get_firebase_activities_for_complaint
        firebase_activities = get_firebase_activities_for_complaint(complaint_id)
    except Exception as e:
        print(f"Error fetching Firebase activities: {e}")

    # Use Django activities as the primary source for now
    activities = django_activities

    # Forms for officers and admins
    status_form = None
    activity_form = None
    reassign_form = None

    if user_role in ['officer', 'admin']:
        if request.method == 'POST':
            if 'update_status' in request.POST:
                status_form = ComplaintStatusUpdateForm(request.POST, instance=complaint)
                if status_form.is_valid():
                    # Save the updated status to Django database
                    updated_complaint = status_form.save()

                    # Save status update to Firebase
                    from utils.firebase import db
                    from firebase_admin import firestore

                    # Create activity data for status update
                    activity_data = {
                        'complaint_id': complaint.id,
                        'officer_uid': user_profile.uid,
                        'officer_email': user_profile.email,
                        'note': f"Status updated to {updated_complaint.status}",
                        'created_at': firestore.SERVER_TIMESTAMP,
                        'status': updated_complaint.status,
                        'activity_type': 'status_update',
                        'has_attachment': False
                    }

                    # Add to Firebase activities collection
                    db.collection('complaint_activities').add(activity_data)

                    # Update the complaint document in Firebase if it exists
                    complaint_ref = db.collection('complaints').document(str(complaint.id))
                    if complaint_ref.get().exists:
                        complaint_ref.update({
                            'status': updated_complaint.status,
                            'last_updated': firestore.SERVER_TIMESTAMP,
                            'last_activity': firestore.SERVER_TIMESTAMP
                        })

                    messages.success(request, "Complaint status updated successfully.")
                    return redirect('complaints:detail', pk=complaint_id)

            elif 'add_activity' in request.POST:
                activity_form = ComplaintActivityForm(request.POST, request.FILES)
                if activity_form.is_valid():
                    # Save to Django database
                    activity = activity_form.save(commit=False)
                    activity.complaint = complaint
                    activity.officer = user_profile
                    activity.save()

                    # Also save to Firebase
                    from utils.firebase import db
                    from firebase_admin import firestore

                    # Create activity data for Firebase
                    activity_data = {
                        'complaint_id': complaint.id,
                        'officer_uid': user_profile.uid,
                        'officer_email': user_profile.email,
                        'note': activity.note or '',
                        'created_at': firestore.SERVER_TIMESTAMP,
                        'status': complaint.status,
                        'has_attachment': bool(activity.attached_file)
                    }

                    # Add to Firebase activities collection
                    db.collection('complaint_activities').add(activity_data)

                    # Also update the complaint document if it exists
                    complaint_ref = db.collection('complaints').document(str(complaint.id))
                    if complaint_ref.get().exists:
                        complaint_ref.update({
                            'last_activity': firestore.SERVER_TIMESTAMP,
                            'status': complaint.status
                        })

                    messages.success(request, "Activity added successfully.")
                    return redirect('complaints:detail', pk=complaint_id)

            elif 'reassign_officer' in request.POST and user_role == 'admin':
                reassign_form = OfficerReassignForm(request.POST, instance=complaint, complaint_location=complaint.location)
                if reassign_form.is_valid():
                    # Save to Django database
                    updated_complaint = reassign_form.save()

                    # Save officer reassignment to Firebase
                    from utils.firebase import db
                    from firebase_admin import firestore

                    # Get the assigned officer's email
                    new_officer_email = updated_complaint.assigned_officer.email if updated_complaint.assigned_officer else 'None'

                    # Create activity data for reassignment
                    activity_data = {
                        'complaint_id': complaint.id,
                        'officer_uid': user_profile.uid,  # Admin who did the reassignment
                        'officer_email': user_profile.email,
                        'note': f"Complaint reassigned to {new_officer_email}",
                        'created_at': firestore.SERVER_TIMESTAMP,
                        'status': updated_complaint.status,
                        'activity_type': 'officer_reassignment',
                        'new_officer_email': new_officer_email,
                        'has_attachment': False
                    }

                    # Add to Firebase activities collection
                    db.collection('complaint_activities').add(activity_data)

                    # Update the complaint document in Firebase if it exists
                    complaint_ref = db.collection('complaints').document(str(complaint.id))
                    if complaint_ref.get().exists:
                        complaint_ref.update({
                            'assigned_officer': new_officer_email,
                            'last_updated': firestore.SERVER_TIMESTAMP,
                            'last_activity': firestore.SERVER_TIMESTAMP
                        })

                    messages.success(request, "Complaint reassigned successfully.")
                    return redirect('complaints:detail', pk=complaint_id)
        else:
            status_form = ComplaintStatusUpdateForm(instance=complaint)
            activity_form = ComplaintActivityForm()

            if user_role == 'admin':
                reassign_form = OfficerReassignForm(instance=complaint, complaint_location=complaint.location)

    context = {
        'complaint': complaint,
        'activities': activities,
        'status_form': status_form,
        'activity_form': activity_form,
        'reassign_form': reassign_form,
        'user_type': user_role,
        'email': request.session.get('firebase_email')
    }

    return render(request, 'complaints/complaint_detail.html', context)