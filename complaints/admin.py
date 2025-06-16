# complaints/admin.py
from django.contrib import admin
from .models import Complaint
from django.contrib import admin
from .models import Complaint, ComplaintActivity

class ComplaintActivityInline(admin.TabularInline):
    model = ComplaintActivity
    extra = 0
    readonly_fields = ['created_at']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'location', 'category', 'user', 'assigned_officer', 'date_submitted']
    list_filter = ['status', 'category', 'location', 'date_submitted']
    search_fields = ['title', 'description', 'user__email', 'assigned_officer__email']
    date_hierarchy = 'date_submitted'
    inlines = [ComplaintActivityInline]

    fieldsets = (
        ('Complaint Information', {
            'fields': ('title', 'description', 'category', 'status', 'image')
        }),
        ('Location & Assignment', {
            'fields': ('location', 'assigned_officer')
        }),
        ('User & Submission', {
            'fields': ('user', 'date_submitted')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ['date_submitted', 'user']
        return ['date_submitted']

@admin.register(ComplaintActivity)
class ComplaintActivityAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'officer', 'created_at']
    list_filter = ['created_at', 'officer']
    search_fields = ['complaint__title', 'note', 'officer__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
