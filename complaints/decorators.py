from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles):
    """
    Decorator for views that checks if the user has the required role.
    If the user doesn't have the required role, they are redirected to the appropriate dashboard.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user is logged in via Firebase
            if not request.session.get('firebase_local_id'):
                messages.error(request, 'You must be logged in to access this page.')
                return redirect('accounts:login')

            # Get user role from session
            user_role = request.session.get('user_role')
            if not user_role:
                messages.error(request, 'Session data is incomplete. Please log in again.')
                return redirect('accounts:login')

            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                # Redirect to appropriate dashboard based on role with a helpful message
                messages.warning(request, f'You do not have permission to access this page. Redirecting to your dashboard.')

                if user_role == 'public':
                    return redirect('complaints:user_dashboard')
                elif user_role == 'officer':
                    return redirect('dashboard:officer_dashboard')
                elif user_role == 'admin':
                    return redirect('dashboard:admin_dashboard')
                else:
                    raise PermissionDenied()

        return _wrapped_view
    return decorator

# Shortcuts for common role checks
def admin_required(view_func):
    return role_required('admin')(view_func)

def officer_required(view_func):
    return role_required(['officer', 'admin'])(view_func)

def public_required(view_func):
    return role_required('public')(view_func)
