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
