from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404, HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from .forms import RegistrationForm, PostCreationForm
from .models import Post, User


# Create your views here.


def test_view(request):
    return render(request=request, template_name='test.html')


def debug_view(request):
    messages.success(request, 'Kek')
    return redirect('test_view')


def logout_user(request):
    logout(request)
    return redirect('main_view')


def search_users(request):
    username = request.GET.get('username')
    if not username:
        return HttpResponseBadRequest('username not provided')

    objects = User.objects.filter(username__istartswith=username).all()[:10]
    print(objects)
    return JsonResponse({'objects': list(obj.username for obj in objects)})


class MainView(View):
    template_name = 'index.html'

    def get(self, request, page=1):
        posts = Post.objects.all()[(page - 1) * 10: page * 10]
        return render(request=request, template_name=self.template_name, context={'posts': posts})


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
            return redirect('main_view')
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
        if not username:
            return Http404()
        else:
            user = get_object_or_404(User, username=username)

        return render(request=request, template_name=self.template_name, context={'user': user})


class SettingsGeneralView(LoginRequiredMixin, View):
    template_name = 'settings_general.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)


class SettingsSocialView(LoginRequiredMixin, View):
    template_name = 'settings_social.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)


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

        if not username:
            return Http404()

        user = User.objects.filter(username=username).annotate(post_count=Count('posts')).first()
        if not user:
            return Http404()

        posts = user.posts.all()[(page - 1) * 10: page * 10]

        return render(request=request, template_name=self.template_name, context={'user': user, 'posts': posts})


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
