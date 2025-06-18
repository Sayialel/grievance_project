from django.http import JsonResponse

def api_login_view(request):
    return JsonResponse({"message": "API Login View Placeholder"})

def api_register_view(request):
    return JsonResponse({"message": "API Register View Placeholder"})

def api_complaints_list_view(request):
    return JsonResponse({"message": "API Complaints List Placeholder"})

def api_complaint_detail_view(request, pk):
    return JsonResponse({"message": f"API Complaint Detail for ID {pk}"})

def complaint_trend_data(request):
    """
    API endpoint to get complaint trend data for charts
    Returns trend data for complaints by month, category, and status
    """
    from datetime import datetime, timedelta
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    from complaints.models import Complaint

    # Get last 6 months of data
    six_months_ago = datetime.now() - timedelta(days=180)

    # Monthly trend data
    monthly_data = (
        Complaint.objects
        .filter(date_submitted__gte=six_months_ago)
        .annotate(month=TruncMonth('date_submitted'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Format the data for the response
    trend_data = {
        'monthly': [
            {
                'month': item['month'].strftime('%b %Y'),
                'count': item['count']
            } for item in monthly_data
        ],
        'categories': [],
        'statuses': []
    }

    # Category distribution
    category_data = (
        Complaint.objects
        .values('category')
        .annotate(count=Count('id'))
        .order_by('category')
    )

    trend_data['categories'] = [
        {
            'category': item['category'],
            'count': item['count']
        } for item in category_data
    ]

    # Status distribution
    status_data = (
        Complaint.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    trend_data['statuses'] = [
        {
            'status': item['status'],
            'count': item['count']
        } for item in status_data
    ]

    return JsonResponse(trend_data)
