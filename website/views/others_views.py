from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect

from website.models import Post
from .view_classes import PagedTemplateView


def test_view(request):
    return render(request=request, template_name='test.html')


def debug_view(request):
    messages.success(request, 'Kek')
    return redirect('test_view')


class MainView(PagedTemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)
        page = context['page']

        qs = Post.objects.filter(
            is_important=True
        )

        context['posts'] = qs.order_by(
            '-created'
        ).select_related(
            'author'
        ).all()[(page - 1) * 10: page * 10]

        context['post_count'] = qs.count()

        context['page_count'] = (context['post_count'] + settings.POSTS_ON_PAGE - 1) // settings.POSTS_ON_PAGE
        return context
