from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Count
from django.http import Http404, HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from guardian.shortcuts import assign_perm

from .decorators import custom_login_required as login_required
from .forms import RegistrationForm, PostCreationForm, CommentCreationForm, TaskCreationForm, FileUploadForm
from .forms import TaskTagForm
from .forms import UserGeneralUpdateForm, UserSocialUpdateForm
from .mixins import CustomLoginRequiredMixin as LoginRequiredMixin, PermissionsRequiredMixin
from .models import Post, User, Task, Contest, TaskTag
from .tokens import deserialize, serialize
from .view_classes import GetPostTemplateViewWithAjax, UsernamePagedTemplateView


def test_view(request):
    return render(request=request, template_name='500.html')


def debug_view(request):
    messages.success(request, 'Kek')
    return redirect('test_view')


@require_GET
def logout_user(request):
    logout(request)
    return redirect('main_view')


@require_GET
def search_users(request):
    username = request.GET.get('username')
    if not username:
        return HttpResponseBadRequest('username not provided')

    objects = User.objects.filter(username__istartswith=username).values_list('username', flat=True)[:10]
    return JsonResponse({'objects': objects})


@require_GET
def search_tags(request):
    tag = request.GET.get('tag')
    if not tag:
        return HttpResponseBadRequest('tag not provided')

    tags = list(TaskTag.objects.filter(name__startswith=tag).values_list('name', flat=True)[:10])
    return JsonResponse({'tags': tags})


@require_POST
@login_required
def leave_comment(request):
    parent_id = request.POST.get('parent_id')
    form = CommentCreationForm(request.POST, request.FILES, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'comment added successfully')
    else:
        for field in form.errors:
            for error in form.errors[field]:
                extra_tags = [field]
                if parent_id:
                    extra_tags.append(str(parent_id))
                else:
                    extra_tags.append('top')
                messages.error(request, error, extra_tags=extra_tags)

    return redirect('post_view', post_id=request.POST.get('post_id', 1))


@require_POST
@login_required
def submit_task(request, task_id):
    flag = request.POST['flag']
    task = Task.objects.filter(id=task_id).prefetch_related('solved_by').first()
    if not task:
        raise Http404()

    response_dict = dict()
    if flag == task.flag:
        response_dict['success'] = True
        if not task.solved_by.filter(id=request.user.id).exists() and task.author != request.user:
            task.solved_by.add(request.user)
            request.user.cost_sum += task.cost
            request.user.save()
        response_dict['next'] = reverse('task_view', kwargs={'task_id': task.id})
    else:
        response_dict['success'] = False
        response_dict['errors'] = {'flag': 'Invalid flag'}
    return JsonResponse(response_dict)


@require_GET
def activate_email(request):
    token = request.GET.get('token')
    user_id = deserialize(token, 'email_confirmation', max_age=86400)

    if user_id is None:
        messages.error(request=request, message='Token is invalid or expired')
        return render(request=request, template_name='account_confirmation.html')

    user = User.objects.filter(id=user_id).first()

    if not user:
        messages.error(request=request, message='Account does not exist.')
        return render(request=request, template_name='account_confirmation.html')

    if not user.is_active:
        messages.success(request=request, message='Account confirmed.')
        user.is_active = True
        user.save()
    else:
        messages.success(request=request, message='Account has already been confirmed.')

    return render(request=request, template_name='account_confirmation.html')


class MainView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)
        page = kwargs.get('page', 1)
        context['page'] = page
        context['posts'] = Post.objects.all().order_by('-created').select_related('author')[(page - 1) * 10: page * 10]
        context['post_count'] = Post.objects.count()
        context['page_count'] = (context['post_count'] + settings.POSTS_ON_PAGE - 1) // settings.POSTS_ON_PAGE
        return context


class UserRegistrationView(TemplateView):
    template_name = 'registration.html'

    @staticmethod
    def post(request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_id = user.id
            email = user.email
            token = serialize(user_id, 'email_confirmation')

            context = {
                'token': token,
                'username': user.username
            }

            message_plain = render_to_string('email_templates/email_confirmation.txt', context)
            message_html = render_to_string('email_templates/email_confirmation.html', context)

            send_mail(
                subject='CTForces account confirmation',
                message=message_plain,
                from_email='CTForces team',
                recipient_list=[email],
                html_message=message_html
            )

            messages.success(request,
                             'User successfully registered! Follow the link in your email to confirm your account!',
                             extra_tags='activation_email_sent')
            return redirect('signin')
        else:
            print(form.errors)
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)
            return redirect('signup')


class EmailResendView(TemplateView):
    template_name = 'resend_email.html'

    @staticmethod
    def post(request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request=request, message='User with this email is not registered', extra_tags='email')
            return redirect('resend_email_view')

        if user.is_active:
            messages.error(request=request, message='Account already activated', extra_tags='email')

        token = serialize(user.id, 'email_confirmation')

        context = {
            'token': token,
            'username': user.username
        }

        message_plain = render_to_string('email_templates/email_confirmation.txt', context)
        message_html = render_to_string('email_templates/email_confirmation.html', context)

        send_mail(
            subject='CTForces account confirmation',
            message=message_plain,
            from_email='CTForces team',
            recipient_list=[email],
            html_message=message_html
        )

        messages.success(request,
                         'Activation email resent.',
                         extra_tags='activation_email_sent')

        return redirect('signin')


class UserLoginView(TemplateView):
    template_name = 'login.html'

    @staticmethod
    def post(request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request=request, username=username, password=password)
        if not user:
            messages.error(request=request, message='Credentials are invalid', extra_tags='password')
            response = redirect('signin')

            if request.GET.get('next'):
                response['Location'] += '?next={}'.format(request.GET.get('next'))

            return response
        elif not user.is_active:
            messages.error(request=request, message='Account is not activated', extra_tags='not_activated')
            response = redirect('signin')

            if request.GET.get('next'):
                response['Location'] += '?next={}'.format(request.GET.get('next'))

            return response

        login(request, user)

        next_page = request.GET.get('next')
        if not next_page:
            next_page = 'main_view'

        return redirect(next_page)


class UserInformationView(TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super(UserInformationView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        user = User.objects.filter(username=username).annotate(friend_count=Count('friends')).first()

        if not user:
            raise Http404()

        context['user'] = user
        return context


class SettingsGeneralView(LoginRequiredMixin, GetPostTemplateViewWithAjax):
    template_name = 'settings_general.html'

    @staticmethod
    def handle_ajax(request):
        form = UserGeneralUpdateForm(request.POST, request.FILES, instance=request.user)
        response_dict = dict()
        if form.is_valid():
            form.save()
            response_dict['success'] = True
            response_dict['next'] = reverse('settings_general_view')
        else:
            print(form.errors)
            response_dict['success'] = False
            response_dict['errors'] = form.errors
        return JsonResponse(response_dict)


class SettingsSocialView(LoginRequiredMixin, GetPostTemplateViewWithAjax):
    template_name = 'settings_social.html'

    def handle_ajax(self, request):
        form = UserSocialUpdateForm(request.POST, instance=request.user)
        response_dict = dict()

        if form.is_valid():
            form.save()
            response_dict['success'] = True
            response_dict['next'] = reverse('settings_social_view')
        else:
            print(form.errors)
            response_dict['success'] = False
            response_dict['errors'] = form.errors

        return JsonResponse(response_dict)


class FriendsView(LoginRequiredMixin, TemplateView):
    template_name = 'friends.html'

    def get_context_data(self, **kwargs):
        context = super(FriendsView, self).get_context_data(**kwargs)
        page = kwargs.get('page', 1)
        context['page'] = page
        friends = self.request.user.friends.all()[(page - 1) * settings.USERS_ON_PAGE: page * settings.USERS_ON_PAGE]
        context['friends'] = friends
        page_count = (self.request.user.friends.count() + settings.USERS_ON_PAGE - 1) // settings.USERS_ON_PAGE
        context['page_count'] = page_count
        return context

    @staticmethod
    def post(request):
        friend_id = request.POST.get('friend_id')
        add = request.POST.get('add', 'true') == 'true'

        if not friend_id:
            return HttpResponseBadRequest('Friend id not provided')

        try:
            friend_id = int(friend_id)
        except ValueError:
            return HttpResponseBadRequest('Invalid friend id')

        friend = get_object_or_404(User, id=friend_id)

        if add:
            request.user.friends.add(friend)
        else:
            request.user.friends.remove(friend)

        request.user.save()
        return HttpResponse('success')


class UserBlogView(TemplateView):
    template_name = 'user_blog.html'

    def get_context_data(self, **kwargs):
        context = super(UserBlogView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        page = kwargs.get('page', 1)
        user = User.objects.filter(username=username).annotate(post_count=Count('posts')).first()
        if not user:
            raise Http404()

        posts = user.posts.all().order_by('-created').select_related('author')[(page - 1) * 10: page * 10]
        page_count = (user.post_count + settings.POSTS_ON_PAGE - 1) // settings.POSTS_ON_PAGE
        context['page'] = page
        context['posts'] = posts
        context['page_count'] = page_count
        return context


class PostCreationView(PermissionsRequiredMixin, TemplateView):
    template_name = 'create_post.html'

    permissions_required = (
        'add_post',
    )

    @staticmethod
    def post(request):

        form = PostCreationForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'post added successfully')
            return redirect('user_blog_view', username=request.user.username)
        else:
            print(form.errors)

            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)

            return redirect('post_creation_view')


class PostView(TemplateView):
    template_name = 'post_view.html'

    def get_context_data(self, **kwargs):
        context = super(PostView, self).get_context_data(**kwargs)
        post_id = kwargs.get('post_id')
        post = Post.objects.filter(id=post_id).prefetch_related('comments', 'author').first()

        if not post:
            raise Http404()

        context['post'] = post
        context['user'] = post.author
        return context


class TaskView(TemplateView):
    template_name = 'task_view.html'

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
    template_name = 'create_task.html'

    permissions_required = (
        'add_task'
    )

    def handle_ajax(self, request):
        task_form = TaskCreationForm(request.POST, user=request.user)
        response_dict = dict()

        if task_form.is_valid():
            task = task_form.save()
            checked_files = []
            checked_tags = []
            error = False

            tags = request.POST.getlist('tags')
            if tags:
                if len(tags) <= 5:
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
                    response_dict['errors']['tags'] = 'Too many tags. Maximum number is 5.'

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
                                checked_files.append(file)

                        else:
                            error = True
                            if not response_dict.get('errors'):
                                response_dict['errors'] = {}
                            response_dict['errors'].update(task_form.errors)
            else:
                error = True
                if not response_dict.get('errors'):
                    response_dict['errors'] = {}
                response_dict['errors']['files'] = 'Too many files. Maximum number is 10.'

            if error:
                task.delete()
                response_dict['success'] = False
                return JsonResponse(response_dict)

            for file in checked_files:
                file.save()
                task.files.add(file)

            for tag in checked_tags:
                task.tags.add(tag)

            assign_perm('view_task', request.user, task)

            response_dict['success'] = True
            response_dict['next'] = reverse('task_view', kwargs={'task_id': task.id})

            return JsonResponse(response_dict)
        else:
            print(task_form.errors)

            response_dict['success'] = False
            response_dict['errors'] = task_form.errors
            return JsonResponse(response_dict)


class TasksArchiveView(TemplateView):
    template_name = 'tasks_archive.html'

    def get_context_data(self, **kwargs):
        context = super(TasksArchiveView, self).get_context_data(**kwargs)
        page = kwargs.get('page', 1)
        tasks = Task.objects.filter(is_published=True).prefetch_related('tags').all()[
                (page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
        page_count = (Task.objects.count() + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        context['page'] = page
        context['tasks'] = tasks
        context['page_count'] = page_count
        return context


class UserTasksView(LoginRequiredMixin, TemplateView):
    template_name = 'users_tasks.html'

    def get_context_data(self, **kwargs):
        context = super(UserTasksView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        page = kwargs.get('page', 1)
        user = User.objects.filter(username=username).annotate(task_count=Count('tasks')).first()
        if not user:
            raise Http404()

        if not self.request.user.has_perm('view_tasks_archive', user):
            raise PermissionDenied()

        tasks = user.tasks.all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
        page_count = (user.task_count + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        context['page'] = page
        context['tasks'] = tasks
        context['page_count'] = page_count

        return context


class UserTopView(TemplateView):
    template_name = 'users_top.html'

    def get_context_data(self, **kwargs):
        context = super(UserTopView, self).get_context_data(**kwargs)
        page = kwargs.get('page', 1)
        users = User.objects.order_by('-cost_sum').all()[
                (page - 1) * settings.USERS_ON_PAGE: page * settings.USERS_ON_PAGE]
        page_count = (User.objects.count() + settings.USERS_ON_PAGE - 1) // settings.USERS_ON_PAGE

        context['page'] = page
        context['users'] = users
        context['page_count'] = page_count

        return context


class PasswordResetEmailView(TemplateView):
    template_name = 'reset_password_email.html'

    @staticmethod
    def post(request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request=request, message='No user with such email exists', extra_tags='email')
            return redirect('password_reset_email')

        token = serialize(user.id, 'password_reset')
        username = user.username

        context = {
            'token': token,
            'username': username
        }

        message_plain = render_to_string('email_templates/password_reset.txt', context)
        message_html = render_to_string('email_templates/password_reset.html', context)

        send_mail(
            subject='CTForces password reset',
            message=message_plain,
            from_email='CTForces team',
            recipient_list=[email],
            html_message=message_html
        )

        messages.success(request,
                         'Follow the link in your email to reset your password!',
                         extra_tags='password_reset_email_sent')

        return redirect('signin')


class PasswordResetPasswordView(TemplateView):
    template_name = 'reset_password_password.html'

    def get_context_data(self, **kwargs):
        context = super(PasswordResetPasswordView, self).get_context_data(**kwargs)
        context['token'] = self.request.GET.get('token')
        return context

    @staticmethod
    def post(request):
        token = request.POST.get('token')
        user_id = deserialize(token, 'password_reset', max_age=86400)

        if user_id is None:
            messages.error(request=request, message='Token is invalid or expired')
            return render(request=request, template_name='reset_password_endpoint.html')

        user = User.objects.filter(id=user_id).first()

        if not user:
            messages.error(request=request, message='Account does not exist.')
            return render(request=request, template_name='reset_password_endpoint.html')
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request=request, message='Password was reset successfully!')
            return render(request=request, template_name='reset_password_endpoint.html')
        else:
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)

            response = redirect('password_reset_password')

            if request.POST.get('token'):
                response['Location'] += '?token={}'.format(request.POST.get('token'))

            return response


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
