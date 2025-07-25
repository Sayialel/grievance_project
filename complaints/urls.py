from django.urls import path
from . import views

app_name = 'complaints'
urlpatterns = [
    path('submit/', views.submit_complaint, name='submit_complaint'),
    path('contact/', views.contact_view, name='contact'),
    path('success/', views.complaint_success, name='complaint_success'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Role-specific dashboards
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('officer/dashboard/', views.officer_dashboard, name='officer_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Complaint detail view (aliases)
    path('complaint/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('complaint/<int:pk>/', views.complaint_detail, name='detail'),

    # Alternative routes
    path('', views.dashboard_view, name='home'),  # Redirects based on role
    path('create/', views.submit_complaint, name='create'),  # Alias for submit_complaint

]