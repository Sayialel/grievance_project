# dashboard/views.py
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from complaints.decorators import admin_required
from complaints.models import Complaint, ComplaintActivity
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
    """Dashboard view for administrators with enhanced filtering and officer management capabilities"""

    # Check if user is logged in and has admin role
    uid = request.session.get('firebase_local_id')
    user_role = request.session.get('user_role')
    email = request.session.get('email')

    # Get the active tab from the query parameter
    active_tab = request.GET.get('tab', 'overview')

    if not uid or user_role != 'admin':
        messages.error(request, 'You must be logged in as an Administrator to access this page.')
        return redirect('accounts:login')

    # Handle complaint reassignment if form submitted
    if request.method == 'POST' and 'reassign_complaint' in request.POST:
        try:
            complaint_id = request.POST.get('complaint_id')
            officer_id = request.POST.get('assigned_officer')
            complaint = Complaint.objects.get(id=complaint_id)
            officer = UserProfile.objects.get(id=officer_id)
            complaint.assigned_officer = officer
            complaint.save()
            messages.success(request, f'Complaint #{complaint_id} has been reassigned to {officer.email}')
        except Exception as e:
            messages.error(request, f'Error reassigning complaint: {str(e)}')
        return redirect('dashboard:admin_dashboard')

    # Get all officers for management and reassignment
    all_officers = UserProfile.objects.filter(role='officer')
    total_officers_count = all_officers.count()

    # Handle officer filter for management section
    officer_location_filter = request.GET.get('officer_location', '')
    if officer_location_filter:
        officers_filtered = all_officers.filter(location=officer_location_filter)
    else:
        officers_filtered = all_officers

    # Get all complaints for administrators
    all_complaints = Complaint.objects.all().order_by('-date_submitted')

    # Enhanced filtering for admin analysis and reporting
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
        # Filter by assigned officer
        if filter_form.cleaned_data.get('assigned_officer'):
            officer_email = filter_form.cleaned_data['assigned_officer']
            filters['assigned_officer__email__icontains'] = officer_email
        # Filter by reporter/user
        if filter_form.cleaned_data.get('reported_by'):
            user_email = filter_form.cleaned_data['reported_by']
            filters['user__email__icontains'] = user_email

        # Full-text search on description and location
        search_text = filter_form.cleaned_data.get('search_text')
        if search_text:
            from django.db.models import Q
            text_filters = Q(description__icontains=search_text) | \
                          Q(location__icontains=search_text) | \
                          Q(user__email__icontains=search_text)
            all_complaints = all_complaints.filter(text_filters)

        if filters:
            all_complaints = all_complaints.filter(**filters)

        # Apply sorting
        sort_by = filter_form.cleaned_data.get('sort_by')
        if sort_by:
            all_complaints = all_complaints.order_by(sort_by)

    # Calculate the percentage for progress bar
    officers_percentage = total_officers_count * 5 if total_officers_count else 0

    # Calculate resolution rate
    total_complaints_count = all_complaints.count()
    resolved_count = all_complaints.filter(status='Resolved').count()
    resolution_rate = 0
    if total_complaints_count > 0:
        resolution_rate = int((resolved_count / total_complaints_count) * 100)

    # Get data for charts
    # Category counts
    category_counts = Complaint.objects.values('category').annotate(count=Count('id'))

    # Location counts
    location_counts = Complaint.objects.values('location').annotate(count=Count('id'))

    # Get officer workloads for chart
    officer_workloads = UserProfile.objects.filter(role='officer').annotate(
        assigned_count=Count('assigned_complaints')
    ).order_by('-assigned_count')[:10]  # Top 10 officers by workload

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

    # For officer reassignment - create a dictionary of officer choices by constituency
    officers_by_location = {}
    for location, location_name in UserProfile.NAIROBI_CONSTITUENCIES:
        location_officers = all_officers.filter(location=location)
        if location_officers.exists():
            officers_by_location[location] = list(location_officers.values('id', 'email'))

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
        'all_officers': all_officers,
        'officers_filtered': officers_filtered,
        'officers_by_location': officers_by_location,
        'officer_location_filter': officer_location_filter,
        'locations': UserProfile.NAIROBI_CONSTITUENCIES,
        'active_tab': active_tab,  # Add the active tab to the context
        'category_counts': category_counts,
        'location_counts': location_counts,
        'officer_workloads': officer_workloads,
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

@admin_required
def edit_officer_view(request, officer_id):
    """Edit Environmental Officer details"""
    officer = get_object_or_404(UserProfile, id=officer_id, role='officer')

    if request.method == 'POST':
        location = request.POST.get('location', officer.location)
        officer.location = location
        officer.save()
        messages.success(request, 'Officer details updated successfully.')
        return redirect(f"{reverse('dashboard:admin_dashboard')}?tab=officers")

    context = {
        'officer': officer,
        'locations': UserProfile.NAIROBI_CONSTITUENCIES,
        'email': request.session.get('firebase_email'),
    }
    return render(request, 'dashboard/edit_officer.html', context)

def statistics_view(request):
    return HttpResponse("Statistics View Placeholder")

def admin_overview_view(request):
    return HttpResponse("Admin Overview View Placeholder")

from django.http import FileResponse
import io
from django.contrib.auth.decorators import login_required
from complaints.decorators import admin_required
@admin_required
def generate_report(request):
    """Generate a PDF report of all complaints using ReportLab"""
    try:
        from complaints.forms import ComplaintFilterForm
        import io
        import datetime
        from django.http import HttpResponse
        from django.shortcuts import redirect
        from django.contrib import messages
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from django.db.models import Q

        # Filter form
        filter_form = ComplaintFilterForm(request.GET or None)
        all_complaints = Complaint.objects.all().order_by('-date_submitted')

        # Apply filters
        if filter_form.is_valid():
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
            if filter_form.cleaned_data.get('assigned_officer'):
                filters['assigned_officer__email__icontains'] = filter_form.cleaned_data['assigned_officer']
            if filter_form.cleaned_data.get('reported_by'):
                filters['user__email__icontains'] = filter_form.cleaned_data['reported_by']

            if filters:
                all_complaints = all_complaints.filter(**filters)

            search_text = filter_form.cleaned_data.get('search_text')
            if search_text:
                all_complaints = all_complaints.filter(
                    Q(description__icontains=search_text) |
                    Q(location__icontains=search_text) |
                    Q(user__email__icontains=search_text)
                )

        # Start generating PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )

        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        styleN = styles['Normal']

        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.white,
            alignment=1,  # Center
        )

        elements = []
        elements.append(Paragraph("Environmental Complaints Report", title_style))
        elements.append(Spacer(1, 0.25 * inch))
        elements.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 0.25 * inch))

        total_count = all_complaints.count()
        pending_count = all_complaints.filter(status='Pending').count()
        in_progress_count = all_complaints.filter(status='In Progress').count()
        resolved_count = all_complaints.filter(status='Resolved').count()

        stats_text = f"Total Complaints: {total_count} | Pending: {pending_count} | In Progress: {in_progress_count} | Resolved: {resolved_count}"
        elements.append(Paragraph(stats_text, subtitle_style))
        elements.append(Spacer(1, 0.25 * inch))

        headers = ['ID', 'Category', 'Description', 'Location', 'Status', 'Date Submitted', 'Assigned Officer', 'Reported By']
        formatted_headers = [Paragraph(header, header_style) for header in headers]
        data = [formatted_headers]

        for complaint in all_complaints:
            officer_email = complaint.assigned_officer.email if complaint.assigned_officer else 'Unassigned'
            reporter_email = complaint.user.email if complaint.user else 'Anonymous'
            formatted_date = complaint.date_submitted.strftime('%Y-%m-%d') if complaint.date_submitted else 'N/A'

            wrapped_row = [
                str(complaint.id),
                complaint.category,
                Paragraph(complaint.description, styleN),
                complaint.location,
                complaint.status,
                formatted_date,
                Paragraph(officer_email, styleN),
                Paragraph(reporter_email, styleN)
            ]
            data.append(wrapped_row)

        col_widths = [
            0.6 * inch,  # ID
            1.0 * inch,  # Category
            3.0 * inch,  # Description
            1.0 * inch,  # Location
            1.0 * inch,  # Status
            1.0 * inch,  # Date Submitted
            1.2 * inch,  # Assigned Officer
            1.2 * inch  # Reported By
        ]

        table = Table(data, colWidths=col_widths, repeatRows=1)

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),   # ID
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),   # Category
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),     # Description
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),   # Location
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),   # Status
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),   # Date Submitted
            ('ALIGN', (6, 1), (6, -1), 'LEFT'),     # Assigned Officer
            ('ALIGN', (7, 1), (7, -1), 'LEFT'),     # Reported By
        ]))

        elements.append(table)
        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="environmental_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        response.write(pdf)
        return response

    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('dashboard:admin_dashboard')


def officer_performance_view(request):
    """Performance dashboard for environmental officer with charts"""
    uid = request.session.get('firebase_local_id')
    user_role = request.session.get('user_role')
    if not uid or user_role != 'officer':
        messages.error(request, 'You must be logged in as an Environmental Officer to access this page.')
        return redirect('accounts:login')

    officer = UserProfile.objects.filter(uid=uid).first()
    if not officer:
        messages.error(request, 'Officer profile not found.')
        return redirect('accounts:login')

    # Complaints assigned to officer's location
    complaints_qs = Complaint.objects.filter(location=officer.location)

    total_assigned = complaints_qs.count()
    resolved_qs = complaints_qs.filter(status='Resolved')
    resolved_count = resolved_qs.count()
    pending_count = complaints_qs.filter(status='Pending').count()
    in_progress_count = complaints_qs.filter(status='In Progress').count()

    # Average resolution time in days for resolved complaints
    from datetime import datetime
    import math
    # Average resolution time calculation skipped (date_resolved not available)
    avg_resolution_days = 0


    # Resolved per month (last 6 months)
    from django.utils import timezone
    now = timezone.now()
    months = []
    resolved_by_month = []
    for i in range(5, -1, -1):
        month_date = (now.replace(day=1) - timezone.timedelta(days=30*i))
        label = month_date.strftime('%b %Y')
        months.append(label)
        month_count = resolved_qs.filter(date_submitted__year=month_date.year, date_submitted__month=month_date.month).count()
        resolved_by_month.append(month_count)

    context = {
        'total_assigned': total_assigned,
        'resolved_count': resolved_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'avg_resolution_days': avg_resolution_days,
        'months_labels': months,
        'resolved_by_month': resolved_by_month,
        'email': request.session.get('firebase_email'),
    }

    return render(request, 'dashboard/officer_performance.html', context)


@admin_required
def officer_management(request):
    """View for managing environmental officers"""
    # Get all officers
    all_officers = UserProfile.objects.filter(role='officer')

    # Handle filter by location
    location_filter = request.GET.get('location', '')
    if location_filter:
        officers = all_officers.filter(location=location_filter)
    else:
        officers = all_officers

    context = {
        'officers': officers,
        'all_officers': all_officers,
        'locations': UserProfile.NAIROBI_CONSTITUENCIES,
        'location_filter': location_filter,
        'email': request.session.get('firebase_email'),
    }

    return render(request, 'dashboard/officer_management.html', context)
