from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Count
from django.http import Http404, HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_GET, require_POST

from .decorators import custom_login_required as login_required
from .forms import RegistrationForm, PostCreationForm, CommentCreationForm, TaskCreationForm, FileUploadForm
from .forms import UserGeneralUpdateForm, UserSocialUpdateForm
from .mixins import CustomLoginRequiredMixin as LoginRequiredMixin
from .models import Post, User, Task
from .tasks import process_file_upload
from .tokens import deserialize, serialize


def test_view(request):
    return render(request=request, template_name='test.html')


def debug_view(request):
    messages.success(request, 'Kek')
    return redirect('test_view')


def logout_user(request):
    logout(request)
    return redirect('main_view')


@require_GET
def search_users(request):
    username = request.GET.get('username')
    if not username:
        return HttpResponseBadRequest('username not provided')

    objects = User.objects.filter(username__istartswith=username).all()[:10]
    return JsonResponse({'objects': list(obj.username for obj in objects)})


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
    task = Task.objects.filter(id=task_id).select_related('solved_by').first()
    if not task:
        raise Http404()

    response_dict = dict()
    if flag == task.flag:
        response_dict['success'] = True

        if not task.solved_by.filter(id=request.user.id).exists():
            task.solved_by.add(request.user)
            request.user.cost_sum += task.cost

    else:
        response_dict['success'] = False
        response_dict['errors'] = ['Invalid flag']
    return JsonResponse(response_dict)


@require_GET
def activate_email(request):
    token = request.GET.get('token')
    user_id = deserialize(token, 'email_confirmation', max_age=86400)

    if user_id is None:
        messages.error(request=request, message='Token is invalid or expired')
        return render(request=request, template_name='account_confirmation.html')

    user = User.objects.get(id=user_id)

    if not user:
        messages.error(request=request, message='Account does not exist')
        return render(request=request, template_name='account_confirmation.html')

    if not user.is_active:
        messages.success(request=request, message='Account confirmed')
        user.is_active = True
    else:
        messages.success(request=request, message='Account already confirmed')

    return render(request=request, template_name='account_confirmation.html')


class MainView(View):
    template_name = 'index.html'

    def get(self, request, page=1):
        posts = Post.objects.all().order_by('-created').select_related('author')[(page - 1) * 10: page * 10]
        post_count = Post.objects.count()
        page_count = (post_count + settings.POSTS_ON_PAGE - 1) // settings.POSTS_ON_PAGE

        return render(request=request, template_name=self.template_name,
                      context={'posts': posts,
                               'page_count': page_count,
                               'page': page})


class UserRegistrationView(View):
    template_name = 'registration.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)

    @staticmethod
    def post(request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_id = user.id
            email = user.email
            token = serialize(user_id, 'email_confirmation')

            context = {
                'token': token
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


class EmailResendView(View):
    template_name = 'resend_email.html'

    def get(self, request):
        return render_to_string(request=request, template_name=self.template_name)

    @staticmethod
    def post(request):
        email = request.POST.get('email')
        user = User.objects.get(email=email)
        if not user:
            messages.error(request=request, message='User with this email is not registered', extra_tags='email')
            return redirect('resend_email_view')

        if user.is_active:
            messages.error(request=request, message='Account already activated', extra_tags='email')

        token = serialize(user.id, 'email_confirmation')

        context = {
            'token': token
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


class UserLoginView(View):
    template_name = 'login.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)

    @staticmethod
    def post(request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request=request, message='Credentials are invalid', extra_tags='password')
            response = redirect('signin')

            if request.GET.get('next'):
                response['Location'] += '?next={}'.format(request.GET.get('next'))

            return response

        login(request, user)

        next_page = request.GET.get('next')
        if not next_page:
            next_page = 'main_view'

        return redirect(next_page)


class UserInformationView(View):
    template_name = 'profile.html'

    def get(self, request, username=None):
        user = User.objects.filter(username=username).annotate(friend_count=Count('friends')).first()

        if not user:
            raise Http404()

        return render(request=request, template_name=self.template_name, context={'user': user})


class SettingsGeneralView(LoginRequiredMixin, View):
    template_name = 'settings_general.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)

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

    @staticmethod
    def handle_default(request):
        form = UserGeneralUpdateForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect('settings_general_view')
        else:
            print(form.errors)
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)

            return redirect('settings_general_view')

    def post(self, request):
        if request.is_ajax():
            return self.handle_ajax(request)
        return self.handle_default(request)


class SettingsSocialView(LoginRequiredMixin, View):
    template_name = 'settings_social.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)

    @staticmethod
    def post(request):
        form = UserSocialUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Information changed successfully')
            return redirect('settings_social_view')
        else:
            print(form.errors)
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)

            return redirect('settings_social_view')


class FriendsView(LoginRequiredMixin, View):
    template_name = 'friends.html'

    def get(self, request, page=1):

        friends = request.user.friends.all()[(page - 1) * settings.USERS_ON_PAGE: page * settings.USERS_ON_PAGE]
        page_count = (request.user.friends.count() + settings.USERS_ON_PAGE - 1) // settings.USERS_ON_PAGE

        return render(request=request, template_name=self.template_name,
                      context={
                          'friends': friends,
                          'page': page,
                          'page_count': page_count
                      })

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


class UserBlogView(View):
    template_name = 'user_blog.html'

    def get(self, request, username=None, page=1):
        user = User.objects.filter(username=username).annotate(post_count=Count('posts')).first()
        if not user:
            raise Http404()

        posts = user.posts.all().order_by('-created').select_related('author')[(page - 1) * 10: page * 10]
        page_count = (user.post_count + settings.POSTS_ON_PAGE - 1) // settings.POSTS_ON_PAGE

        return render(request=request, template_name=self.template_name,
                      context={'user': user,
                               'posts': posts,
                               'page': page,
                               'page_count': page_count})


class PostCreationView(LoginRequiredMixin, View):
    template_name = 'create_post.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)

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


class PostView(View):
    template_name = 'post_view.html'

    def get(self, request, post_id):
        post = Post.objects.filter(id=post_id).prefetch_related('comments', 'author').first()

        if not post:
            raise Http404()

        return render(request=request, template_name=self.template_name,
                      context={'post': post, 'user': post.author})


class TaskView(View):
    template_name = 'task_view.html'

    def get(self, request, task_id):
        task = Task.objects.filter(id=task_id).first()
        if not task:
            raise Http404()

        return render(request=request, template_name=self.template_name,
                      context={'task': task})


class TaskCreationView(LoginRequiredMixin, View):
    template_name = 'create_task.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)

    @staticmethod
    def handle_ajax(request):
        task_form = TaskCreationForm(request.POST, user=request.user)

        response_dict = dict()

        if task_form.is_valid():
            task = task_form.save(commit=False)

            checked_files = []
            error = False

            if len(request.FILES) <= 10:
                for filename in request.FILES:
                    file_form = FileUploadForm({'file_field': request.FILES[filename]}, task=task, user=request.user)
                    if file_form.is_valid():
                        if not error:
                            checked_files.append(file_form.save(commit=False))
                    else:
                        error = True
                        if not response_dict.get('errors'):
                            response_dict['errors'] = []

                        response_dict['errors'] += task_form.errors
            else:
                error = True
                response_dict['errors'] = [{'file_count': 'Too many files. Maximum number is 10.'}]
            if error:
                response_dict['success'] = False
                return JsonResponse(response_dict)

            task.save()

            response_dict['success'] = True
            response_dict['next'] = reverse('task_view', kwargs={'task_id': task.id})

            process_file_upload.delay(checked_files=checked_files)
            return JsonResponse(response_dict)
        else:
            print(task_form.errors)

            response_dict['success'] = False
            response_dict['errors'] = task_form.errors
            return JsonResponse(response_dict)

    @staticmethod
    def handle_default(request):
        task_form = TaskCreationForm(request.POST, user=request.user)
        if task_form.is_valid():
            task = task_form.save(commit=False)

            checked_files = []
            error = False

            if len(request.FILES) <= 10:
                for filename in request.FILES:
                    file_form = FileUploadForm({'file_field': request.FILES[filename]}, task=task, user=request.user)
                    if file_form.is_valid():
                        checked_files.append(file_form.save(commit=False))
                    else:
                        error = True
                        for field in task_form.errors:
                            for error in task_form.errors[field]:
                                messages.error(request, error, extra_tags=['file', filename])
            else:
                error = True
                messages.error(request, 'Too many files. Maximum number is 10.', extra_tags='file_count')
            if error:
                return redirect('task_creation_view')

            process_file_upload.delay(checked_files=checked_files, task=task)
            return redirect('main_view')
        else:
            print(task_form.errors)

            for field in task_form.errors:
                for error in task_form.errors[field]:
                    messages.error(request, error, extra_tags=field)
            return redirect('task_creation_view')

    def post(self, request):
        if request.is_ajax():
            return self.handle_ajax(request)
        return self.handle_default(request)


class TasksArchiveView(View):
    template_name = 'tasks_archive.html'

    def get(self, request, page=1):
        tasks = Task.objects.filter(is_published=True)[
                (page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
        page_count = (Task.objects.count() + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        return render(request=request, template_name=self.template_name,
                      context={
                          'tasks': tasks,
                          'page': page,
                          'page_count': page_count
                      })


class UserTasksView(LoginRequiredMixin, View):
    template_name = 'users_tasks.html'

    def get(self, request, username=None, page=1):
        user = User.objects.get(username=username).annotate(task_count=Count('tasks'))
        if not user:
            raise Http404()
        if user != request.user:
            raise PermissionDenied()
        tasks = user.tasks.all()[(page - 1) * settings.TASKS_ON_PAGE: page * settings.TASKS_ON_PAGE]
        page_count = (user.task_count + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        return render(request=request, template_name=self.template_name,
                      context={
                          'tasks': tasks,
                          'page': page,
                          'page_count': page_count
                      })


class UserTopView(View):
    template_name = 'users_top.html'

    def get(self, request, page=1):
        users = User.objects.order_by('-rating').all()[
                (page - 1) * settings.USERS_ON_PAGE: page * settings.USERS_ON_PAGE]
        page_count = (User.objects.count() + settings.USERS_ON_PAGE - 1) // settings.USERS_ON_PAGE
        return render(request=request, template_name=self.template_name,
                      context={
                          'users': users,
                          'page': page,
                          'page_count': page_count
                      })
