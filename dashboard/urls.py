from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('admin-overview/', views.admin_overview_view, name='admin_overview'),
]
