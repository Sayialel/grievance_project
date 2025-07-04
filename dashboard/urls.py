# dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('officer/', views.officer_dashboard, name='officer_dashboard'),
    path('officer/performance/', views.officer_performance_view, name='officer_performance'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('admin-overview/', views.admin_overview_view, name='admin_overview'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('officer-management/', views.officer_management, name='officer_management'),
    path('officer/<int:officer_id>/edit/', views.edit_officer_view, name='edit_officer'),
]
