from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('login/', views.api_login_view, name='api_login'),
    path('register/', views.api_register_view, name='api_register'),
    path('complaints/', views.api_complaints_list_view, name='api_complaints_list'),
    path('complaints/<int:pk>/', views.api_complaint_detail_view, name='api_complaint_detail'),
    path('complaints/trend-data/', views.complaint_trend_data, name='complaint_trend_data'),
]
