from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView
from guardian.shortcuts import get_objects_for_user

from website.decorators import custom_login_required as login_required
from website.forms import ContestForm
from website.mixins import PermissionsRequiredMixin
from website.models import User, Contest, Task
from .view_classes import UsernamePagedTemplateView, GetPostTemplateViewWithAjax


@require_GET
@login_required
def get_task(request):
    task_id = request.GET.get('id')
    task = list(get_objects_for_user(
        request.user,
        'view_task',
        Task
    ).filter(id=task_id).only('name').first())

    return JsonResponse({'task': task})


class ContestMainView(TemplateView):
    template_name = 'contest_view.html'

    def get_context_data(self, **kwargs):
        context = super(ContestMainView, self).get_context_data(**kwargs)
        contest_id = kwargs.get('contest_id')
        contest = Contest.objects.filter(id=contest_id, is_published=True).first()
        if not contest:
            raise Http404()

        tasks = contest.tasks.annotate(
            number_solved=Count('contesttaskrelationship__solved')
        ).all()

        context['contest'] = contest
        context['tasks'] = tasks
        return context


class ContestScoreboardView(TemplateView):
    template_name = 'contest_scoreboard.html'

    def get_context_data(self, **kwargs):
        context = super(ContestScoreboardView, self).get_context_data(**kwargs)
        contest_id = kwargs.get('contest_id')
        page = kwargs.get('page', 1)
        contest = Contest.objects.filter(id=contest_id, is_published=True).first()
        if not contest:
            raise Http404()

        tasks = contest.tasks.annotate(
            number_solved=Count('contesttaskrelationship__solved')
        ).all()

        users = contest.participants.annotate(cost_sum=Sum('contesttaskrelationship__cost')) \
                    .order_by('-cost_sum')[(page - 1) * settings.USERS_ON_PAGE:page * settings.USERS_ON_PAGE]

        context['contest'] = contest
        context['tasks'] = tasks
        context['users'] = users

        return context


class ContestsMainListView(TemplateView):
    template_name = 'main_contests_list_view.html'

    def get_context_data(self, **kwargs):
        context = super(ContestsMainListView, self).get_context_data(**kwargs)
        page = context['page']

        qs = Contest.objects.filter(is_published=True)
        context['page_count'] = (qs.count() + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE
        context['contests'] = qs.all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
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

        context['contests'] = user.contests.all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
        context['page_count'] = (user.contest_count + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE
        return context


class ContestCreationView(PermissionsRequiredMixin, GetPostTemplateViewWithAjax):
    permissions_required = (
        'create_contest',
    )

    template_name = 'create_contest.html'

    def handle_default(self, request, *args, **kwargs):

        task_ids = request.POST['tasks']
        tasks = []
        for task_id in task_ids:
            task = Task.objects.filter(id=task_id).first()
            if not task:
                raise Http404()

            if not request.user.has_perm('view_task', task):
                raise PermissionDenied()

            tasks.append(task)

        form = ContestForm(request.POST, user=request.user)
        if form.is_valid():
            contest = form.save()
            contest.tasks.add(tasks)
            messages.success(request=request, message='Contest created successfully.')
            return redirect('contest_view', kwargs={'contest_id': contest.id})
        else:
            print(form.errors)
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)
            return redirect('create_contest')
