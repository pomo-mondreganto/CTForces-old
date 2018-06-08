from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def custom_login_required(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.is_ajax():
                raise PermissionDenied()
            else:
                path = request.build_full_path()
                redirect_field_name = 'next'
                return redirect_to_login(path, settings.LOGIN_URL, redirect_field_name)
        return f(request, *args, **kwargs)

    return wrapper
