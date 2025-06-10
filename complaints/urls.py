from django.urls import path
from . import views

urlpatterns = [
    path('', views.complaint_list_view, name='complaint_list'),
    path('create/', views.create_complaint_view, name='create_complaint'),
    path('<int:complaint_id>/', views.complaint_detail_view, name='complaint_detail'),
    path('<int:complaint_id>/status/', views.update_complaint_status_view, name='update_complaint_status'),
]
