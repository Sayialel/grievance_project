
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Already initialized in settings.py so:
db = firestore.client()

def get_user_by_email(email):
    try:
        return auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        return None

def verify_id_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception:
        return None
