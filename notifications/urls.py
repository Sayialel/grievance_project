from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list_view, name='notifications'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read_view, name='mark_notification_read'),
    path('delete/<int:notification_id>/', views.delete_notification_view, name='delete_notification'),
]
