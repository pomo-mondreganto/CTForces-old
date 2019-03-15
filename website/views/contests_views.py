from django.conf import settings
from django.db.models import IntegerField, BooleanField
from django.db.models import Q, Sum, Case, When, Value as V, Prefetch, Count, Subquery, OuterRef
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from django.utils.datetime_safe import datetime
from guardian.shortcuts import get_objects_for_user, assign_perm

from website.decorators import custom_login_required as login_required
from website.forms import ContestForm
from website.mixins import AjaxPermissionsRequiredMixin
from website.models import User, Contest, Task, TaskTag, ContestTaskRelationship
from .view_classes import PagedTemplateView, UsernamePagedTemplateView, GetPostTemplateViewWithAjax


@require_GET
@login_required
def get_task(request):
    try:
        task_id = int(request.GET.get('id'))
    except ValueError:
        task_id = -1

    task = get_objects_for_user(
        request.user,
        'view_task',
        Task
    ).filter(id=task_id).prefetch_related(Prefetch(
        'tags', queryset=TaskTag.objects.only('name')
    )).only('id', 'name').first()

    if not task:
        return JsonResponse({'task': {}})

    return JsonResponse({'task': {'id': task.id, 'name': task.name, 'tags': list(tag.name for tag in task.tags.all())}})


@require_POST
@login_required
def submit_contest_flag(request, contest_id, task_id):
    flag = request.POST.get('flag', '').strip()
    contest = Contest.objects.filter(Q(is_running=True) | Q(is_finished=True),
                                     id=contest_id,
                                     is_published=True
                                     ).prefetch_related('tasks').first()
    if not contest:
        raise Http404()

    task = contest.tasks.filter(id=task_id).first()
    if not task:
        raise Http404()

    response_dict = dict()
    if flag == task.flag:
        response_dict['success'] = True
        if not request.user.has_perm('change_task', task):
            if contest.is_running:
                relationship = task.contest_task_relationship.filter(contest=contest).first()

                if not relationship:
                    raise Http404()
                if not relationship.solved.filter(id=request.user.id).exists():
                    relationship.solved.add(request.user)
            if not task.solved_by.filter(id=request.user.id).exists():
                task.solved_by.add(request.user)
                request.user.last_solve = datetime.now()
                request.user.save()

        response_dict['next'] = reverse('contest_view', kwargs={'contest_id': contest_id})
    else:
        response_dict['success'] = False
        response_dict['errors'] = {'flag': 'Invalid flag'}
    return JsonResponse(response_dict)


@require_POST
@login_required
def register_for_contest(request, contest_id):
    contest = Contest.objects.filter(id=contest_id).only(
        'is_registration_open',
        'is_finished',
        'is_running'
    ).first()

    if not contest:
        raise Http404()

    result = dict()

    if not contest.is_registration_open or request.user.has_perm('change_contest', contest):
        result['success'] = False
        result['next'] = reverse('contests_main_list_view')
        return JsonResponse(result)

    if contest.is_running or not contest.is_finished:
        if not contest.participants.filter(id=request.user.id).exists():
            contest.participants.add(request.user)
            assign_perm('can_participate_in_contest', request.user, contest)

    result['success'] = True
    if contest.is_running:
        result['next'] = reverse('contest_view', kwargs=dict(contest_id=contest_id))
    else:
        result['next'] = reverse('contests_main_list_view')

    return JsonResponse(result)


class ContestMainView(TemplateView):
    template_name = 'contest_templates/contest_view.html'

    def get_context_data(self, **kwargs):
        context = super(ContestMainView, self).get_context_data(**kwargs)
        contest_id = kwargs.get('contest_id')
        contest = Contest.objects.filter(
            Q(is_running=True) | Q(is_finished=True),
            id=contest_id,
            is_published=True
        ).order_by().union(
            get_objects_for_user(self.request.user, 'view_unstarted_contest', Contest).filter(
                id=contest_id
            )
        ).first()
        if not contest:
            raise Http404()

        tasks = contest.tasks.annotate(
            solved_count=Count(
                'contest_task_relationship__solved',
                filter=Q(contest_task_relationship__solved__contests_participated=contest),
                distinct=True
            ),
            is_solved_by_user=Sum(
                Case(
                    When(
                        contest_task_relationship__solved__id=(self.request.user.id or -1),
                        then=1
                    ),
                    default=V(0),
                    output_field=BooleanField()
                )
            ),
            contest_cost=Subquery(
                ContestTaskRelationship.objects.filter(
                    contest=contest,
                    task_id=OuterRef('id')
                ).values('cost')
            )
        ).all()
        context['contest'] = contest
        context['tasks'] = tasks
        return context


class ContestScoreboardView(PagedTemplateView):
    template_name = 'contest_templates/contest_scoreboard.html'

    def get_context_data(self, **kwargs):
        context = super(ContestScoreboardView, self).get_context_data(**kwargs)
        contest_id = kwargs.get('contest_id')
        page = context['page']
        contest = Contest.objects.filter(
            Q(is_running=True) | Q(is_finished=True),
            id=contest_id,
            is_published=True
        ).order_by().union(
            get_objects_for_user(self.request.user, 'view_unstarted_contest', Contest).filter(
                id=contest_id
            )
        ).first()

        if not contest:
            raise Http404

        users = contest.participants.prefetch_related(
            Prefetch(
                'contest_task_relationship',
                queryset=ContestTaskRelationship.objects.only('contest', 'cost')
            )
        ).annotate(
            cost_sum=Sum(
                Case(
                    When(
                        contest_task_relationship__contest=contest,
                        then='contest_task_relationship__cost'
                    ),
                    default=V(0),
                    output_field=IntegerField()
                )
            ),
        ).order_by(
            '-cost_sum',
            'last_solve',
        )[(page - 1) * settings.USERS_ON_PAGE:page * settings.USERS_ON_PAGE]

        start_number = (page - 1) * settings.USERS_ON_PAGE

        context['start_number'] = start_number
        context['contest'] = contest
        context['users'] = users

        return context


class ContestsMainListView(PagedTemplateView):
    template_name = 'index_templates/main_contests_list_view.html'

    def get_context_data(self, **kwargs):
        context = super(ContestsMainListView, self).get_context_data(**kwargs)
        page = context['page']

        qs = Contest.objects.filter(is_published=True)

        context['page_count'] = (qs.filter(
            is_finished=True
        ).count() + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        context['running_contests'] = qs.filter(
            is_running=True
        ).all()

        context['finished_contests'] = qs.filter(
            is_finished=True
        ).all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]

        return context


class UserContestListView(UsernamePagedTemplateView):
    template_name = 'profile_templates/user_contests.html'

    def get_context_data(self, **kwargs):
        context = super(UserContestListView, self).get_context_data(**kwargs)
        username = context['username']
        page = context['page']
        user = User.objects.filter(username=username).annotate(contest_count=Count('contests')).first()

        if not user:
            raise Http404()

        context['user'] = user

        if self.request.user.has_perm('view_contests_archive', user):
            context['contests'] = user.contests.all()[
                                  (page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
            context['page_count'] = (user.contest_count + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE
        else:
            qs = user.contests.filter(
                is_published=True,
                is_finished=True
            )
            context['contests'] = qs.all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
            context['page_count'] = (qs.count() + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        return context


class ContestCreationView(AjaxPermissionsRequiredMixin, GetPostTemplateViewWithAjax):
    permissions_required = (
        'add_contest',
    )

    template_name = 'contest_templates/create_contest.html'

    def handle_ajax(self, request, *args, **kwargs):
        task_ids = request.POST.getlist('tasks')
        task_tags = request.POST.getlist('tags')
        task_costs = request.POST.getlist('costs')

        result = dict()

        if len(task_ids) != len(task_tags) or len(task_ids) != len(task_costs) or not len(task_ids):
            result['success'] = False
            result['errors'] = {'tasks': 'Need to add at least 1 task to contest.'}
            result['next'] = reverse('create_contest')
            return JsonResponse(result)

        tasks = []
        for i, task_id in enumerate(task_ids):

            try:
                task_id = int(task_id)
            except ValueError:
                continue

            task = Task.objects.filter(id=task_id).first()

            if not task or not request.user.has_perm('view_task', task):
                result['success'] = False
                result['errors'] = {'tasks': 'Invalid task.'}
                result['next'] = reverse('create_contest')
                return JsonResponse(result)

            tag_name = task_tags[i]
            tag = TaskTag.objects.filter(name=tag_name).first()
            if not tag:
                result['success'] = False
                result['errors'] = {'tags': 'Invalid tag, only existing tags are allowed.'}
                result['next'] = reverse('create_contest')
                return JsonResponse(result)

            cost = task_costs[i]
            try:
                cost = int(cost)
                if cost < 0 or cost > 9999:
                    raise ValueError()
            except ValueError:
                result['success'] = False
                result['errors'] = {'costs': 'Invalid cost. Cost must be an integer from 0 to 9999'}
                result['next'] = reverse('create_contest')
                return JsonResponse(result)

            tasks.append((task, tag, cost))

        form = ContestForm(request.POST, user=request.user)
        if form.is_valid():
            contest = form.save()
            for task in tasks:
                relationship = ContestTaskRelationship(task=task[0],
                                                       contest=contest,
                                                       tag=task[1],
                                                       cost=task[2])
                relationship.save()

            assign_perm('change_contest', request.user, contest)
            assign_perm('view_unstarted_contest', request.user, contest)
            assign_perm('can_participate_in_contest', request.user, contest)

            result['next'] = reverse('contest_view', kwargs=dict(contest_id=contest.id))
            result['success'] = True
            return JsonResponse(result)
        else:
            print(form.errors)

            result['next'] = reverse('create_contest')
            result['success'] = False
            result['errors'] = form.errors
            return JsonResponse(result)


class ContestTaskView(TemplateView):
    template_name = 'task_templates/contest_task.html'

    def get_context_data(self, **kwargs):
        context = super(ContestTaskView, self).get_context_data(**kwargs)
        contest_id = kwargs.get('contest_id')
        contest = Contest.objects.filter(
            Q(is_running=True) | Q(is_finished=True),
            id=contest_id,
            is_published=True
        ).order_by().union(
            get_objects_for_user(self.request.user, 'view_unstarted_contest', Contest).filter(
                id=contest_id
            )
        ).first()
        if not contest:
            raise Http404

        task_id = kwargs.get('task_id')
        task = contest.tasks.filter(id=task_id).first()
        if not task:
            raise Http404()

        context['contest'] = contest
        context['task'] = task
        return context
