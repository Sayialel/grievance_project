# dashboard/views.py
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from complaints.models import Complaint
from accounts.models import UserProfile

def officer_dashboard(request):
    """Dashboard view for environmental officers"""

    # Check if user is logged in and has officer role
    uid = request.session.get('firebase_local_id')
    user_role = request.session.get('user_role')

    if not uid or user_role != 'officer':
        messages.error(request, 'You must be logged in as an Environmental Officer to access this page.')
        return redirect('accounts:login')

    # Get the officer's profile to get their assigned location
    profile = UserProfile.objects.filter(uid=uid).first()
    if not profile:
        messages.error(request, 'Officer profile not found. Please log in again.')
        return redirect('accounts:login')

    location = profile.location
    print(f"Officer location: {location}")

    # Get all complaints in the system for debugging
    all_complaints = Complaint.objects.all()
    print(f"Total complaints in system: {all_complaints.count()}")

    # Get complaints assigned to this officer's location
    if location:
        # Get complaints by location, whether explicitly assigned to this officer or not
        assigned_complaints = Complaint.objects.filter(location=location).order_by('-date_submitted')
        print(f"Complaints found for location {location}: {assigned_complaints.count()}")

        # If no complaints found with location filter, show all complaints for debugging
        if assigned_complaints.count() == 0:
            print("No complaints found for this location. Checking if any complaints exist in system.")
            # Check if complaints exist in other locations
            other_locations = Complaint.objects.exclude(location=location)
            print(f"Complaints in other locations: {other_locations.count()}")
            # For testing, you could temporarily show all complaints
            # assigned_complaints = Complaint.objects.all().order_by('-date_submitted')
    else:
        assigned_complaints = Complaint.objects.none()
        print("No location found for officer, no complaints assigned")

    # Debug complaint statuses in the system
    if all_complaints.exists():
        sample_complaint = all_complaints.first()
        print(f"Sample complaint status: {sample_complaint.status}")
        print(f"Sample complaint location: {sample_complaint.location}")
        print(f"Complaint status choices: {[status for status, _ in Complaint._meta.get_field('status').choices]}")

    context = {
        'assigned_complaints': assigned_complaints,
        'total_assigned': assigned_complaints.count(),
        'pending_count': assigned_complaints.filter(status='Pending').count(),
        'in_progress_count': assigned_complaints.filter(status='In Progress').count(),
        'resolved_count': assigned_complaints.filter(status='Resolved').count(),
        'officer_location': dict(UserProfile.NAIROBI_CONSTITUENCIES).get(location, 'Unknown'),
        'email': request.session.get('firebase_email'),
    }

    return render(request, 'dashboard/officer_dashboard.html', context)

def admin_dashboard(request):
    """Dashboard view for administrators"""

    # Check if user is logged in and has admin role
    uid = request.session.get('firebase_local_id')
    user_role = request.session.get('user_role')

    if not uid or user_role != 'admin':
        messages.error(request, 'You must be logged in as an Administrator to access this page.')
        return redirect('accounts:login')

    # Get all complaints for administrators
    all_complaints = Complaint.objects.all().order_by('-date_submitted')

    # Filtering for admin analysis and reporting
    from complaints.forms import ComplaintFilterForm
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

        if filters:
            all_complaints = all_complaints.filter(**filters)

        # Apply sorting
        sort_by = filter_form.cleaned_data.get('sort_by')
        if sort_by:
            all_complaints = all_complaints.order_by(sort_by)

    # Get all officers
    all_officers = UserProfile.objects.filter(role='officer')
    total_officers_count = all_officers.count()

    # Calculate the percentage for progress bar (replacing the need for mul filter)
    officers_percentage = total_officers_count * 5 if total_officers_count else 0

    # Calculate resolution rate
    total_complaints_count = all_complaints.count()
    resolved_count = all_complaints.filter(status='Resolved').count()
    resolution_rate = 0
    if total_complaints_count > 0:
        resolution_rate = int((resolved_count / total_complaints_count) * 100)

    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(all_complaints, 10)  # 10 complaints per page
    page = request.GET.get('page')
    try:
        complaints = paginator.page(page)
    except PageNotAnInteger:
        complaints = paginator.page(1)
    except EmptyPage:
        complaints = paginator.page(paginator.num_pages)

    context = {
        'all_complaints': complaints,  # Now paginated
        'filter_form': filter_form,
        'total_complaints': total_complaints_count,
        'pending_count': all_complaints.filter(status='Pending').count(),
        'in_progress_count': all_complaints.filter(status='In Progress').count(),
        'resolved_count': resolved_count,
        'total_officers': total_officers_count,
        'officers_percentage': officers_percentage,
        'resolution_rate': resolution_rate,
        'email': request.session.get('firebase_email'),
    }

    return render(request, 'dashboard/admin_dashboard.html', context)
def dashboard_view(request):
    """Main dashboard view that redirects to role-specific dashboards"""
    # Check if user is logged in via Firebase
    uid = request.session.get('firebase_local_id')
    if not uid:
        messages.error(request, 'You must be logged in to access the dashboard.')
        return redirect('accounts:login')

    # Get user role from session
    user_role = request.session.get('user_role')

    # Redirect based on role
    if user_role == 'officer':
        return redirect('dashboard:officer_dashboard')
    elif user_role == 'admin':
        return redirect('dashboard:admin_dashboard')
    else:  # public user
        return redirect('complaints:user_dashboard')

def statistics_view(request):
    return HttpResponse("Statistics View Placeholder")

def admin_overview_view(request):
    return HttpResponse("Admin Overview View Placeholder")
