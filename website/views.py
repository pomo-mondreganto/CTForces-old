from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
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
            print('kek')
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


class UserSearchView(View):

    @staticmethod
    def get(request):
        username = request.GET.get('username')
        if not username:
            return HttpResponseBadRequest('username not provided')

        objects = User.objects.filter(username__istartswith=username).all()[:10]
        return JsonResponse({'objects': obj.username for obj in objects})
