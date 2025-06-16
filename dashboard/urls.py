from django.urls import path
from . import views

app_name = 'dashboard'  # Required for namespacing

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('admin-overview/', views.admin_overview_view, name='admin_overview'),
]
