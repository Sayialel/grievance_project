from django.db import models
from django.conf import settings
from accounts.models import UserProfile

class ComplaintCategory(models.TextChoices):
    AIR = 'air', 'Air Pollution'
    WATER = 'water', 'Water Pollution'
    WASTE = 'waste', 'Waste Management'
    NOISE = 'noise', 'Noise Pollution'
    OTHER = 'other', 'Other'

# ✅ Fixed ComplaintStatus: removed `choices = None`
class ComplaintStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    IN_PROGRESS = 'In Progress', 'In Progress'
    RESOLVED = 'Resolved', 'Resolved'
    CLOSED = 'Closed', 'Closed'

class Complaint(models.Model):
    # Get the same constituency choices from UserProfile
    NAIROBI_CONSTITUENCIES = UserProfile.NAIROBI_CONSTITUENCIES

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='submitted_complaints')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=50, choices=NAIROBI_CONSTITUENCIES, default='other')
    category = models.CharField(
        max_length=50,
        choices=ComplaintCategory.choices,
        default=ComplaintCategory.OTHER
    )
    image = models.ImageField(upload_to='complaint_attachments/', blank=True, null=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=ComplaintStatus.choices,
        default=ComplaintStatus.PENDING
    )
    assigned_officer = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_complaints',
        limit_choices_to={'role': 'officer'}
    )

    def __str__(self):
        return f"{self.title} - {self.status}"

class ComplaintActivity(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='activities')
    officer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'role': 'officer'})
    note = models.TextField(blank=True, null=True)
    attached_file = models.FileField(upload_to='complaint_activities/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Activity for {self.complaint.title} by {self.officer.email}"

    class Meta:
        verbose_name_plural = "Complaint Activities"
        ordering = ['-created_at']
