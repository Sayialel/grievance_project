# dashboard/utils.py
from complaints.models import Complaint
from accounts.models import UserProfile
from django.db.models import Count, Avg, F, ExpressionWrapper, fields
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

def get_complaints_by_status():
    """Get count of complaints grouped by status"""
    status_counts = Complaint.objects.values('status').annotate(count=Count('id')).order_by('status')
    return status_counts

def get_complaints_by_category():
    """Get count of complaints grouped by category"""
    category_counts = Complaint.objects.values('category').annotate(count=Count('id')).order_by('category')
    return category_counts

def get_complaints_by_location():
    """Get count of complaints grouped by location"""
    location_counts = Complaint.objects.values('location').annotate(count=Count('id')).order_by('location')
    return location_counts

def get_officer_workload():
    """Get count of assigned complaints per officer"""
    officer_workload = UserProfile.objects.filter(role='officer').annotate(
        workload=Count('assigned_complaints')
    ).values('email', 'workload').order_by('-workload')[:10]
    return officer_workload

def get_monthly_complaint_counts(months=6):
    """Get monthly complaint counts for the last X months"""
    # Calculate the date X months ago
    start_date = datetime.now() - timedelta(days=30*months)

    # Group complaints by month and count
    monthly_counts = Complaint.objects.filter(
        date_submitted__gte=start_date
    ).annotate(
        month=TruncMonth('date_submitted')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    return monthly_counts

def generate_pdf_report_data():
    """Gather all data needed for PDF report"""
    data = {
        'status_counts': get_complaints_by_status(),
        'category_counts': get_complaints_by_category(),
        'location_counts': get_complaints_by_location(),
        'officer_workload': get_officer_workload(),
        'monthly_counts': get_monthly_complaint_counts(),
        'total_complaints': Complaint.objects.count(),
        'pending_count': Complaint.objects.filter(status='Pending').count(),
        'in_progress_count': Complaint.objects.filter(status='In Progress').count(),
        'resolved_count': Complaint.objects.filter(status='Resolved').count(),
        'total_officers': UserProfile.objects.filter(role='officer').count(),
        'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    return data
