from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

class CustomUserAdmin(UserAdmin):
    model = UserProfile
    list_display = ('username', 'email', 'is_staff', 'is_verified')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'profile_image', 'is_verified')}),
    )

admin.site.register(UserProfile, CustomUserAdmin)
