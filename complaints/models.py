# complaints/models.py

from django.db import models
from django.conf import settings

class ComplaintCategory(models.TextChoices):
    AIR = 'air', 'Air Pollution'
    WATER = 'water', 'Water Pollution'
    WASTE = 'waste', 'Waste Management'
    NOISE = 'noise', 'Noise Pollution'
    OTHER = 'other', 'Other'


class ComplaintStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    IN_PROGRESS = 'In Progress', 'In Progress'
    RESOLVED = 'Resolved', 'Resolved'
    CLOSED = 'Closed', 'Closed'


class Complaint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
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

    def __str__(self):
        return f"{self.title} - {self.status}"
