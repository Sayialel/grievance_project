from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles):
    """
    Decorator for views that checks if the user has the required role.
    If the user doesn't have the required role, they are redirected to the login page.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            if not hasattr(request.user, 'userprofile'):
                raise PermissionDenied()

            user_role = request.user.userprofile.role
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
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
