# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('public', 'Public User'),
        ('officer', 'Environmental Officer'),
        ('admin', 'Administrator'),
    ]

    NAIROBI_CONSTITUENCIES = [
        ('westlands', 'Westlands'),
        ('dagoretti_north', 'Dagoretti North'),
        ('langata', 'Langata'),
        ('kibra', 'Kibra'),
        ('roysambu', 'Roysambu'),
        ('kasarani', 'Kasarani'),
        ('ruaraka', 'Ruaraka'),
        ('embakasi_south', 'Embakasi South'),
        ('embakasi_north', 'Embakasi North'),
        ('embakasi_central', 'Embakasi Central'),
        ('embakasi_east', 'Embakasi East'),
        ('embakasi_west', 'Embakasi West'),
        ('makadara', 'Makadara'),
        ('kamukunji', 'Kamukunji'),
        ('starehe', 'Starehe'),
        ('mathare', 'Mathare'),
        ('other', 'Other'),
    ]

    uid = models.CharField(max_length=128, unique=True, null=True, blank=True)  # Firebase UID
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='public')
    location = models.CharField(max_length=50, choices=NAIROBI_CONSTITUENCIES, default='other')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.email} ({self.role})"

    def get_active_complaints_count(self):
        """Return the count of active complaints assigned to this officer"""
        if self.role != 'officer':
            return 0
        return self.assigned_complaints.filter(status__in=['Pending', 'In Progress']).count()

    def __str__(self):
        return f"{self.email} ({self.role})"
