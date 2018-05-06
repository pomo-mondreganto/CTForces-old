from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View

from .forms import RegistrationForm
from .models import Post, User


# Create your views here.


def test_view(request):
    return render(request=request, template_name='test.html')


def debug_view(request):
    messages.success(request, 'Kek')
    return redirect('test_view')


def logout_view(request):
    logout(request)
    return redirect('main_view')


class MainView(View):
    template_name = 'index.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name, context={'posts': Post.objects.all()[:10]})


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
            return redirect('signin')

        login(request, user)
        return redirect('main_view')


class UserInformationView(View):
    template_name = 'profile.html'

    def get(self, request, username=None):
        if not username:
            if request.user:
                user = request.user
            else:
                return Http404()
        else:
            user = User.objects.filter(username=username).first()
            if not user:
                return Http404()

        return render(request=request, template_name=self.template_name, context={'user': user})


class SettingsView(View):
    template_name = 'settings.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)


class FriendsView(View):
    template_name = 'friends.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)

    @staticmethod
    def post(request):
        friend_id = request.POST.get('user_id')
        if not friend_id or:
            messages.error(request, 'user_id not provided')
            return redirect('friends_view')
        try:
            user = User.objects.filter(id=int(friend_id))
            if not user:
                raise ValueError()
        except ValueError:
            messages.error(request, 'invalid user_id')
            return redirect('friends_view')

        request.user.friends.add(user)
        request.user.save()
