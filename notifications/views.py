from django.http import HttpResponse

def notifications_list_view(request):
    return HttpResponse("Notifications List View Placeholder")

def mark_notification_read_view(request, notification_id):
    return HttpResponse(f"Mark Notification as Read Placeholder for ID {notification_id}")

def delete_notification_view(request, notification_id):
    return HttpResponse(f"Delete Notification Placeholder for ID {notification_id}")
