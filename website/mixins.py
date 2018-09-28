from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse


class CustomLoginRequiredMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        if self.raise_exception or self.request.is_ajax():
            return HttpResponse('Unauthorized', status=401)
        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())


class PermissionsRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.has_perms(self.permissions_required or []):
            self.handle_no_permission()
        return super(PermissionsRequiredMixin, self).dispatch(request, *args, **kwargs)


class AjaxPermissionsRequiredMixin(PermissionsRequiredMixin, CustomLoginRequiredMixin):
    pass
