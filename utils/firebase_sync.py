# utils/firebase_sync.py

from utils.firebase import db
from firebase_admin import firestore
from complaints.models import Complaint, ComplaintActivity

from accounts.models import UserProfile
import logging

logger = logging.getLogger(__name__)


def sync_complaint_to_firebase(complaint):
    """
    Synchronize a complaint from Django database to Firebase Firestore
    """
    try:
        complaint_data = {
            'id': complaint.id,
            'title': complaint.title,
            'description': complaint.description,
            'location': complaint.location,
            'location_display': complaint.get_location_display(),
            'category': complaint.category,
            'status': complaint.status,
            'date_submitted': firestore.SERVER_TIMESTAMP ,
            'user_uid': complaint.user.uid if complaint.user else None,
            'user_email': complaint.user.email if complaint.user else None,
            'has_image': bool(complaint.image),
            'assigned_officer': complaint.assigned_officer.email if complaint.assigned_officer else None
        }

        db.collection('complaints').document(str(complaint.id)).set(complaint_data)
        logger.info(f"Complaint {complaint.id} synced to Firebase.")
        return complaint_data

    except Exception as e:
        logger.error(f"Error syncing complaint {complaint.id} to Firebase: {e}")
        return None


def sync_activity_to_firebase(activity, activity_type='note'):
    """
    Synchronize a complaint activity from Django database to Firebase Firestore
    """
    try:
        activity_data = {
            'complaint_id': activity.complaint.id,
            'officer_uid': activity.officer.uid if activity.officer else None,
            'officer_email': activity.officer.email if activity.officer else None,
            'note': activity.note or "",
            'created_at': firestore.SERVER_TIMESTAMP ,
            'status': activity.complaint.status,
            'activity_type': activity_type,
            'has_attachment': bool(activity.attached_file)
        }

        db.collection('complaint_activities').add(activity_data)
        logger.info(f"Activity for complaint {activity.complaint.id} synced to Firebase.")

        # Update the related complaint document
        complaint_ref = db.collection('complaints').document(str(activity.complaint.id))
        complaint_snapshot = complaint_ref.get()

        if complaint_snapshot.exists:
            complaint_ref.update({
                'last_activity': activity_data['created_at'],
                'status': activity.complaint.status
            })
            logger.info(f"Updated complaint {activity.complaint.id} with latest activity info.")

        return activity_data

    except Exception as e:
        logger.error(f"Error syncing activity for complaint {activity.complaint.id} to Firebase: {e}")
        return None


def sync_all_complaints_to_firebase():
    """
    Synchronize all complaints from Django database to Firebase Firestore
    """
    complaints = Complaint.objects.all()
    synced_count = 0

    for complaint in complaints:
        if sync_complaint_to_firebase(complaint):
            synced_count += 1

    logger.info(f"Total complaints synced to Firebase: {synced_count}")
    return synced_count


def sync_all_activities_to_firebase():
    """
    Synchronize all complaint activities from Django database to Firebase Firestore
    """
    activities = ComplaintActivity.objects.all().order_by('created_at')
    synced_count = 0

    for activity in activities:
        if sync_activity_to_firebase(activity):
            synced_count += 1

    logger.info(f"Total complaint activities synced to Firebase: {synced_count}")
    return synced_count


def get_firebase_activities_for_complaint(complaint_id):
    """
    Retrieve all activities for a complaint from Firebase
    """
    try:
        activities_ref = db.collection('complaint_activities')

        # Use positional arguments only for compatibility with current SDK
        query = activities_ref.where('complaint_id', '==', complaint_id).order_by(
            'created_at', direction=firestore.Query.DESCENDING)

        activities = query.stream()

        return [activity.to_dict() for activity in activities]

    except Exception as e:
        logger.error(f"Error fetching activities for complaint {complaint_id} from Firebase: {e}")
        return []
