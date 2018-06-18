from django.http import Http404
from django.views.generic.base import TemplateView


class GetPostTemplateViewWithAjax(TemplateView):

    def handle_default(self, *args, **kwargs):
        raise NotImplemented()

    def handle_ajax(self, *args, **kwargs):
        raise NotImplemented()

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            return self.handle_ajax(request, *args, **kwargs)
        return self.handle_default(request, *args, **kwargs)


class UsernamePagedTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(UsernamePagedTemplateView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        page = kwargs.get('page', 1)
        if not username:
            raise Http404()

        context['page'] = page
        context['username'] = username

        return context
