from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


class CustomLoginRequiredMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        if self.raise_exception or self.request.is_ajax():
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
