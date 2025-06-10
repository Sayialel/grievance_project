# complaints/admin.py
from django.contrib import admin
from .models import Complaint

admin.site.register(Complaint)
