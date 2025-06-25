# utils/context_processors.py

from accounts.models import UserProfile

def user_role(request):
    """
    Add user role to context for all templates
    """
    context = {'user_role': None}

    if request.session.get('firebase_local_id'):
        # First try to get from session for performance
        if 'user_role' in request.session:
            context['user_role'] = request.session.get('user_role')
        else:
            # If not in session, get from database
            uid = request.session.get('firebase_local_id')
            profile = UserProfile.objects.filter(uid=uid).first()
            if profile:
                context['user_role'] = profile.role
                # Store in session for future requests
                request.session['user_role'] = profile.role

    return context
