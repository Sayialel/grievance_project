# utils/firebase_sync.py

from utils.firebase import db
from firebase_admin import firestore
from complaints.models import Complaint, ComplaintActivity
from accounts.models import UserProfile

def sync_complaint_to_firebase(complaint):
    """
    Synchronize a complaint from Django database to Firebase Firestore
    """
    # Create complaint data for Firebase
    complaint_data = {
        'id': complaint.id,
        'title': complaint.title,
        'description': complaint.description,
        'location': complaint.location,
        'location_display': complaint.get_location_display(),
        'category': complaint.category,
        'status': complaint.status,
        'date_submitted': firestore.SERVER_TIMESTAMP if not complaint.date_submitted else 
                           firestore.Timestamp.from_datetime(complaint.date_submitted),
        'user_uid': complaint.user.uid if complaint.user else None,
        'user_email': complaint.user.email if complaint.user else None,
        'has_image': bool(complaint.image),
        'assigned_officer': complaint.assigned_officer.email if complaint.assigned_officer else None
    }

    # Add to Firebase complaints collection
    db.collection('complaints').document(str(complaint.id)).set(complaint_data)
    return complaint_data

def sync_activity_to_firebase(activity, activity_type='note'):
    """
    Synchronize a complaint activity from Django database to Firebase Firestore
    """
    # Create activity data for Firebase
    activity_data = {
        'complaint_id': activity.complaint.id,
        'officer_uid': activity.officer.uid if activity.officer else None,
        'officer_email': activity.officer.email if activity.officer else None,
        'note': activity.note or "",
        'created_at': firestore.SERVER_TIMESTAMP if not activity.created_at else 
                      firestore.Timestamp.from_datetime(activity.created_at),
        'status': activity.complaint.status,
        'activity_type': activity_type,
        'has_attachment': bool(activity.attached_file)
    }

    # Add to Firebase activities collection
    activity_ref = db.collection('complaint_activities').add(activity_data)

    # Update the complaint document in Firebase
    complaint_ref = db.collection('complaints').document(str(activity.complaint.id))
    if complaint_ref.get().exists:
        complaint_ref.update({
            'last_activity': activity_data['created_at'],
            'status': activity.complaint.status
        })

    return activity_data

def sync_all_complaints_to_firebase():
    """
    Synchronize all complaints from Django database to Firebase Firestore
    This is useful for initial data migration or recovery
    """
    complaints = Complaint.objects.all()
    synced_count = 0

    for complaint in complaints:
        sync_complaint_to_firebase(complaint)
        synced_count += 1

    return synced_count

def sync_all_activities_to_firebase():
    """
    Synchronize all complaint activities from Django database to Firebase Firestore
    This is useful for initial data migration or recovery
    """
    activities = ComplaintActivity.objects.all().order_by('created_at')
    synced_count = 0

    for activity in activities:
        sync_activity_to_firebase(activity)
        synced_count += 1

    return synced_count

def get_firebase_activities_for_complaint(complaint_id):
    """
    Retrieve all activities for a complaint from Firebase
    """
    activities_ref = db.collection('complaint_activities')
    query = activities_ref.where('complaint_id', '==', complaint_id).order_by('created_at', direction=firestore.Query.DESCENDING)
    activities = query.stream()

    return [activity.to_dict() for activity in activities]
