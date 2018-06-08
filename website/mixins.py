from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse


class CustomLoginRequiredMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        if self.raise_exception or self.request.is_ajax():
            return HttpResponse('Unauthorized', 401)
        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
