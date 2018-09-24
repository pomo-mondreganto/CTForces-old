from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.db.models import Sum, Case, When, BooleanField, Value as V
from django.db.models.query import Prefetch
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils.datetime_safe import datetime
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from guardian.shortcuts import assign_perm

from website.decorators import custom_login_required as login_required
from website.forms import TaskForm, FileUploadForm
from website.forms import TaskTagForm
from website.mixins import CustomLoginRequiredMixin as LoginRequiredMixin, PermissionsRequiredMixin
from website.models import User, Task, TaskTag, File
from .view_classes import GetPostTemplateViewWithAjax, PagedTemplateView


@require_GET
def search_tags(request):
    tag = request.GET.get('tag')
    if not tag:
        return HttpResponseBadRequest('tag not provided')

    tags = list(TaskTag.objects.filter(name__startswith=tag).values_list('name', flat=True)[:10])
    return JsonResponse({'tags': tags})


@require_POST
@login_required
def submit_task(request, task_id):
    flag = request.POST.get('flag', '').strip()
    task = Task.objects.filter(id=task_id).prefetch_related('solved_by').first()
    if not task:
        raise Http404()

    response_dict = dict()
    if flag == task.flag:
        response_dict['success'] = True
        if not task.solved_by.filter(id=request.user.id).exists() and not request.user.has_perm('edit_task', task):
            task.solved_by.add(request.user)
            request.user.last_solve = datetime.now()
            request.user.save()

        response_dict['next'] = reverse('task_view', kwargs={'task_id': task.id})
    else:
        response_dict['success'] = False
        response_dict['errors'] = {'flag': 'Invalid flag'}
    return JsonResponse(response_dict)


class TaskView(TemplateView):
    template_name = 'task_templates/task_view.html'

    def get_context_data(self, **kwargs):
        context = super(TaskView, self).get_context_data(**kwargs)
        task_id = kwargs.get('task_id')
        task = Task.objects.filter(id=task_id).prefetch_related('tags').first()

        if not task:
            raise Http404()

        if not task.is_published and not self.request.user.has_perm('view_task', task):
            raise PermissionDenied()

        context['task'] = task
        return context


class TaskCreationView(PermissionsRequiredMixin, GetPostTemplateViewWithAjax):
    template_name = 'task_templates/create_task.html'

    permissions_required = (
        'add_task',
    )

    def handle_ajax(self, request, **kwargs):
        task_form = TaskForm(request.POST, user=request.user)
        response_dict = dict()

        if task_form.is_valid():
            task = task_form.save()
            checked_files = []
            checked_tags = []
            error = False

            tags = request.POST.getlist('tags')
            if tags:
                if 1 <= len(tags) <= 5:
                    for tag_name in tags:
                        tag_form = TaskTagForm({'name': tag_name})
                        if tag_form.is_valid():
                            tag, created = TaskTag.objects.get_or_create(**tag_form.cleaned_data)
                            checked_tags.append(tag)
                        else:
                            error = True
                            if not response_dict.get('errors'):
                                response_dict['errors'] = {}
                            response_dict['errors'].update(tag_form.errors)
                else:
                    error = True
                    if not response_dict.get('errors'):
                        response_dict['errors'] = {}
                    response_dict['errors']['tags'] = 'You can add from 1 to 5 tags to task.'

            if len(request.FILES) <= 10:
                for filename in request.FILES:
                    for file_object in request.FILES.getlist(filename):
                        data = {
                            'file_field': file_object,
                        }

                        file_form = FileUploadForm(request.POST, data)
                        if file_form.is_valid():
                            if not error:
                                file = file_form.save(commit=False)
                                file.name = file_object.name
                                file.owner = request.user
                                file.upload_time = datetime.now()
                                file.task = task
                                checked_files.append(file)

                        else:
                            error = True
                            if not response_dict.get('errors'):
                                response_dict['errors'] = {}
                            response_dict['errors'].update(file_form.errors)
            else:
                error = True
                if not response_dict.get('errors'):
                    response_dict['errors'] = {}
                response_dict['errors']['files'] = 'Too many files. Maximum number is 10.'

            if error:
                task.delete()
                response_dict['success'] = False
                return JsonResponse(response_dict)

            File.objects.bulk_create(checked_files)
            task.tags.add(*checked_tags)

            assign_perm('view_task', request.user, task)
            assign_perm('change_task', request.user, task)

            response_dict['success'] = True
            response_dict['next'] = reverse('task_view', kwargs={'task_id': task.id})
            return JsonResponse(response_dict)
        else:
            print(task_form.errors)

            response_dict['success'] = False
            response_dict['errors'] = task_form.errors
            return JsonResponse(response_dict)


class TasksArchiveView(PagedTemplateView):
    template_name = 'index_templates/tasks_archive.html'

    def get_context_data(self, **kwargs):
        context = super(TasksArchiveView, self).get_context_data(**kwargs)
        page = context['page']

        tasks = Task.objects.filter(
            is_published=True
        ).prefetch_related(
            'tags'
        ).annotate(
            is_solved_by_user=Sum(
                Case(
                    When(
                        solved_by__id=(self.request.user.id or -1),
                        then=1
                    ),
                    default=V(0),
                    output_field=BooleanField()
                ),
            ),
            solved_count=Count(
                'solved_by',
                distinct=True
            )
        ).order_by(
            '-publication_time', '-id'
        ).all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]

        page_count = (Task.objects.filter(
            is_published=True).count() + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE
        context['start_number'] = (page - 1) * settings.TASKS_ON_PAGE
        context['tasks'] = tasks
        context['page_count'] = page_count
        return context


class UserTasksView(LoginRequiredMixin, PagedTemplateView):
    template_name = 'profile_templates/users_tasks.html'

    def get_context_data(self, **kwargs):
        context = super(UserTasksView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        page = context['page']
        user = User.objects.filter(
            username=username
        ).annotate(
            task_count=Count(
                'tasks'
            )
        ).first()
        if not user:
            raise Http404()

        if not self.request.user.has_perm('view_tasks_archive', user):
            raise PermissionDenied()

        tasks = user.tasks.annotate(
            solved_count=Count(
                'solved_by'
            )
        ).prefetch_related(
            'tags'
        ).order_by(
            '-id'
        ).all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]

        page_count = (user.task_count + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        context['user'] = user
        context['tasks'] = tasks
        context['page_count'] = page_count

        return context


class TaskEditView(LoginRequiredMixin, GetPostTemplateViewWithAjax):
    template_name = 'task_templates/task_edit.html'

    def get_context_data(self, **kwargs):
        context = super(TaskEditView, self).get_context_data(**kwargs)
        task_id = kwargs.get('task_id')
        if task_id is None:
            raise Http404()

        task = Task.objects.filter(id=task_id).prefetch_related(
            Prefetch(
                'files',
                queryset=File.objects.only(
                    'id',
                    'name',
                    'file_field'
                ).all()
            )
        ).first()

        if not task:
            raise Http404()

        if not self.request.user.has_perm('change_task', task):
            raise PermissionDenied()

        context['task'] = task

        return context

    def handle_ajax(self, request, *args, **kwargs):
        task_id = kwargs.get('task_id')
        if task_id is None:
            raise Http404()

        task = Task.objects.filter(id=task_id).prefetch_related('files', 'tags').annotate(
            file_count=Count(
                'files',
                distinct=True
            ),
            tag_count=Count(
                'tags',
                distinct=True
            )
        ).first()

        if not task:
            raise Http404()

        if not self.request.user.has_perm('change_task', task):
            raise PermissionDenied()

        response_dict = dict()

        task_form = TaskForm(request.POST, user=request.user, instance=task)
        if task_form.is_valid():
            task_form.save(commit=False)

            add_files = []
            if request.FILES.get('add_files'):
                add_files = request.FILES.getlist('add_files')

            remove_files = []
            if request.POST.get('remove_files'):
                remove_files = list(set(request.POST.getlist('remove_files')))

            checked_files = []
            new_file_count = task.file_count - len(remove_files) + len(add_files)
            if new_file_count > 10:
                response_dict['success'] = False

                if not response_dict.get('errors'):
                    response_dict['errors'] = {}

                response_dict['errors']['files'] = 'Too many files. Maximum number is 10.'
                return JsonResponse(response_dict)

            error = False
            for file_object in add_files:
                data = {
                    'file_field': file_object,
                }

                file_form = FileUploadForm(request.POST, data)
                if file_form.is_valid():
                    if not error:
                        file = file_form.save(commit=False)
                        file.name = file_object.name
                        file.owner = request.user
                        file.upload_time = datetime.now()
                        file.task = task

                        checked_files.append(file)
                else:
                    print(data)
                    error = True

                    if not response_dict.get('errors'):
                        response_dict['errors'] = {}

                    response_dict['errors'].update(task_form.errors)

            if error:
                response_dict['success'] = False
                return JsonResponse(response_dict)

            checked_tags = []
            tags = request.POST.getlist('tags')
            if tags:
                if 1 <= len(tags) <= 5:
                    for tag_name in tags:
                        tag_form = TaskTagForm({'name': tag_name})
                        if tag_form.is_valid():
                            tag, created = TaskTag.objects.get_or_create(**tag_form.cleaned_data)
                            checked_tags.append(tag)
                        else:
                            error = True
                            if not response_dict.get('errors'):
                                response_dict['errors'] = {}
                            response_dict['errors'].update(tag_form.errors)
                else:
                    error = True
                    if not response_dict.get('errors'):
                        response_dict['errors'] = {}
                    response_dict['errors']['tags'] = 'You can add from 1 to 5 tags to task.'

            if error:
                response_dict['success'] = False
                return JsonResponse(response_dict)

            task.tags.clear()
            task.tags.add(*checked_tags)
            task.files.remove(*list(File.objects.filter(id__in=list(remove_files)).all()))
            File.objects.bulk_create(checked_files)
            task.save()
            response_dict['success'] = True
            response_dict['next'] = reverse('task_view', kwargs={'task_id': task.id})
            return JsonResponse(response_dict)
        else:
            print(task_form.errors)

            response_dict['success'] = False
            response_dict['errors'] = task_form.errors
            return JsonResponse(response_dict)


class TaskSolvedView(PagedTemplateView):
    template_name = 'task_templates/task_solved.html'

    def get_context_data(self, **kwargs):
        context = super(TaskSolvedView, self).get_context_data(**kwargs)
        page = context['page']
        task_id = kwargs.get('task_id')
        if task_id is None:
            raise Http404()

        task = Task.objects.filter(
            id=task_id
        ).prefetch_related(
            'solved_by'
        ).annotate(
            solved_by_count=Count(
                'solved_by'
            )
        ).first()

        if not task:
            raise Http404()

        users = task.solved_by.all()[(page - 1) * settings.USERS_ON_PAGE: page * settings.USERS_ON_PAGE]

        page_count = (task.solved_by_count + settings.USERS_ON_PAGE - 1) // settings.USERS_ON_PAGE

        context['task_id'] = task_id
        context['users'] = users
        context['page_count'] = page_count

        return context


class UserSolvedTasksView(PagedTemplateView):
    template_name = 'profile_templates/user_solved_tasks.html'

    def get_context_data(self, **kwargs):
        context = super(UserSolvedTasksView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        page = context['page']

        user = User.objects.filter(
            username=username
        ).annotate(
            task_count=Count(
                'solved_tasks'
            )
        ).first()

        if not user:
            raise Http404()

        tasks = user.solved_tasks.order_by(
            '-id'
        ).all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
        page_count = (user.task_count + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        context['user'] = user
        context['tasks'] = tasks
        context['page_count'] = page_count

        return context
