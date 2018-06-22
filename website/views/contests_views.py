from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import Http404
from django.views.generic import TemplateView

from website.models import User, Contest
from .view_classes import UsernamePagedTemplateView


class ContestView(TemplateView):
    template_name = 'contest_view.html'

    def get_context_data(self, **kwargs):
        context = super(ContestView, self).get_context_data(**kwargs)
        contest_id = kwargs.get('contest_id')
        contest = Contest.objects.filter(id=contest_id, is_published=True).prefetch_related('tasks').first()
        if not contest:
            raise Http404()
        context['contest'] = contest
        return context


class UserContestsView(UsernamePagedTemplateView):
    template_name = 'user_contests.html'

    def get_context_data(self, **kwargs):
        context = super(UserContestsView, self).get_context_data(**kwargs)
        username = context['username']
        page = context['page']
        user = User.objects.filter(username=username).annotate(contest_count=Count('contests')).first()

        if not user:
            raise Http404()

        if not self.request.user.has_perm('view_contests_archive', user):
            raise PermissionDenied()

        context['contents'] = user.contests.all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
        context['page_count'] = (user.contest_count + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE
        return context
