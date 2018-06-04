from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404, HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.http import require_GET, require_POST

from .forms import RegistrationForm, PostCreationForm, CommentCreationForm, TaskCreationForm, FileUploadForm
from .forms import UserGeneralUpdateForm, UserSocialUpdateForm, AvatarUploadForm
from .models import Post, User, Task
from .tasks import process_file_upload


# Create your views here.


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
                messages.error(request, error, extra_tags=extra_tags)

    return redirect('post_view', post_id=request.POST.get('post_id', 1))


@require_POST
@login_required
def change_avatar(request):
    print(request.POST, request.FILES)
    form = AvatarUploadForm(request.POST, request.FILES, instance=request.user)
    response_dict = dict()
    if form.is_valid():
        form.save()
        response_dict['success'] = True
        status_code = 200
    else:
        response_dict['success'] = False
        response_dict['errors'] = form.errors
        status_code = 400

    return JsonResponse(response_dict, status=status_code)


class MainView(View):
    template_name = 'index.html'

    def get(self, request, page=1):
        posts = Post.objects.all().select_related('author')[(page - 1) * 10: page * 10]
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
            form.save()
            messages.success(request, 'User successfully registered! There will be email confirmation sometime')
            return redirect('signin')
        else:
            print(form.errors)
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)
            return redirect('signup')


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
    def post(request):
        form = UserGeneralUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Information changed successfully')
            return redirect('settings_general_view')
        else:
            print(form.errors)
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)

            return redirect('settings_general_view')


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

    def get(self, request):
        return render(request=request, template_name=self.template_name)

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

        posts = user.posts.all().select_related('author')[(page - 1) * 10: page * 10]
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
    def post(request):
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


class TasksArchiveView(View):
    template_name = 'tasks_archive.html'

    def get(self, request, page=1):
        tasks = Task.objects.filter(is_published=True)[(page - 1) * 10: page * 10]
        page_count = (Task.objects.count() + settings.TASKS_ON_PAGE - 1) // settings.TASKS_ON_PAGE

        return render(request=request, template_name=self.template_name,
                      context={
                          'tasks': tasks,
                          'page': page,
                          'page_count': page_count
                      })
