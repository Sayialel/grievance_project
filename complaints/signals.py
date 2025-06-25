# complaints/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from complaints.models import Complaint, ComplaintActivity
from utils.firebase_sync import sync_complaint_to_firebase, sync_activity_to_firebase

@receiver(post_save, sender=Complaint)
def sync_complaint_on_save(sender, instance, created, **kwargs):
    """
    Automatically sync complaint to Firebase when saved
    """
    sync_complaint_to_firebase(instance)

@receiver(post_save, sender=ComplaintActivity)
def sync_activity_on_save(sender, instance, created, **kwargs):
    """
    Automatically sync complaint activity to Firebase when saved
    """
    sync_activity_to_firebase(instance)
