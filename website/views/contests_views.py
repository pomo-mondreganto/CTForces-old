from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView
from guardian.shortcuts import get_objects_for_user

from website.decorators import custom_login_required as login_required
from website.mixins import PermissionsRequiredMixin
from website.models import User, Contest, Task
from .view_classes import UsernamePagedTemplateView, GetPostTemplateViewWithAjax


@require_GET
@login_required
def search_tasks(request):
    name = request.GET.get('name')
    tasks = list(get_objects_for_user(
        request.user,
        'view_task',
        Task
    ).filter(name__istartswith=name).values_list('name', flat=True)[:10])

    return JsonResponse({'tasks': tasks})


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


class ContestCreationView(PermissionsRequiredMixin, GetPostTemplateViewWithAjax):
    permissions_required = (
        'create_contest',
    )

    template_name = 'create_contest.html'

    def handle_ajax(self, request, *args, **kwargs):
        raise NotImplemented
