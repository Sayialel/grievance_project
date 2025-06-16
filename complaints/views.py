from django.contrib import messages
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

@login_required
def dashboard_view(request):
    # Redirect based on user role
    user_role = request.user.userprofile.role
    if user_role == 'admin':
        return redirect('complaints:admin_dashboard')
    elif user_role == 'officer':
        return redirect('complaints:officer_dashboard')
    else:  # public user
        return redirect('complaints:user_dashboard')

@login_required
def submit_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Create complaint but don't save yet
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()

            # Auto assign an officer
            assigned_officer = auto_assign_officer(complaint)

            if assigned_officer:
                messages.success(request, f"Your complaint has been submitted and assigned to an officer in {complaint.get_location_display()}.")
            else:
                messages.success(request, "Your complaint has been submitted. An officer will be assigned soon.")

            return redirect('complaints:complaint_success')
    else:
        form = ComplaintForm()

    return render(request, 'complaints/submit_complaint.html', {'form': form})

@login_required
def complaint_success(request):
    return render(request, 'complaints/complaint_success.html')

@login_required
def user_dashboard(request):
    """Dashboard for public users to view their own complaints"""
    user_complaints = Complaint.objects.filter(user=request.user).order_by('-date_submitted')

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

        if filters:
            user_complaints = user_complaints.filter(**filters)

        # Apply sorting
        sort_by = filter_form.cleaned_data.get('sort_by')
        if sort_by:
            user_complaints = user_complaints.order_by(sort_by)

    # Pagination
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
        'filter_form': filter_form,
        'user_type': 'public'
    }
    return render(request, 'complaints/complaint_list.html', context)

@officer_required
def officer_dashboard(request):
    """Dashboard for officers to view complaints assigned to them"""
    officer = request.user.userprofile

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
        'user_type': 'officer'
    }
    return render(request, 'complaints/complaint_list.html', context)

@admin_required
def admin_dashboard(request):
    """Dashboard for admins to view all complaints"""
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
        'user_type': 'admin'
    }
    return render(request, 'complaints/complaint_list.html', context)

@login_required
def complaint_detail(request, pk):
    """View for displaying complaint details and handling updates"""
    complaint = get_object_or_404(Complaint, pk=pk)
    user = request.user
    user_role = user.userprofile.role

    # Check permissions
    if user_role == 'public' and complaint.user != user:
        messages.error(request, "You don't have permission to view this complaint.")
        return redirect('complaints:user_dashboard')
    elif user_role == 'officer' and complaint.assigned_officer != user.userprofile:
        messages.error(request, "This complaint is not assigned to you.")
        return redirect('complaints:officer_dashboard')

    # Get activities
    activities = complaint.activities.all().order_by('-created_at')

    # Forms for officers and admins
    status_form = None
    activity_form = None
    reassign_form = None

    if user_role in ['officer', 'admin']:
        if request.method == 'POST':
            if 'update_status' in request.POST:
                status_form = ComplaintStatusUpdateForm(request.POST, instance=complaint)
                if status_form.is_valid():
                    status_form.save()
                    messages.success(request, "Complaint status updated successfully.")
                    return redirect('complaints:complaint_detail', pk=pk)

            elif 'add_activity' in request.POST:
                activity_form = ComplaintActivityForm(request.POST, request.FILES)
                if activity_form.is_valid():
                    activity = activity_form.save(commit=False)
                    activity.complaint = complaint
                    activity.officer = user.userprofile
                    activity.save()
                    messages.success(request, "Activity added successfully.")
                    return redirect('complaints:complaint_detail', pk=pk)

            elif 'reassign_officer' in request.POST and user_role == 'admin':
                reassign_form = OfficerReassignForm(request.POST, instance=complaint, complaint_location=complaint.location)
                if reassign_form.is_valid():
                    reassign_form.save()
                    messages.success(request, "Complaint reassigned successfully.")
                    return redirect('complaints:complaint_detail', pk=pk)
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
        'user_type': user_role
    }

    return render(request, 'complaints/complaint_detail.html', context)