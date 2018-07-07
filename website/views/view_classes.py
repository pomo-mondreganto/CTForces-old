from django.http import Http404
from django.views.generic.base import TemplateView


class GetPostTemplateViewWithAjax(TemplateView):

    def handle_default(self, request, *args, **kwargs):
        raise NotImplemented()

    def handle_ajax(self, request, *args, **kwargs):
        raise NotImplemented()

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            return self.handle_ajax(request, *args, **kwargs)
        return self.handle_default(request, *args, **kwargs)


class PagedTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(PagedTemplateView, self).get_context_data(**kwargs)
        page = kwargs.get('page', 1)

        if page < 1:
            raise Http404()

        context['page'] = page
        return context


class UsernamePagedTemplateView(PagedTemplateView):
    def get_context_data(self, **kwargs):
        context = super(UsernamePagedTemplateView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        if not username:
            raise Http404()

        context['username'] = username

        return context
