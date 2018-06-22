from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import SetPasswordForm
from django.core.mail import send_mail
from django.db.models import Sum, Value as V
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from website.forms import RegistrationForm
from website.forms import UserGeneralUpdateForm, UserSocialUpdateForm
from website.mixins import CustomLoginRequiredMixin as LoginRequiredMixin
from website.models import User
from website.tokens import deserialize, serialize
from .view_classes import GetPostTemplateViewWithAjax


@require_GET
def logout_user(request):
    logout(request)
    return redirect('main_view')


@require_GET
def search_users(request):
    username = request.GET.get('username')
    if not username:
        return HttpResponseBadRequest('username not provided')

    objects = list(User.objects.filter(username__istartswith=username).values_list('username', flat=True)[:10])
    return JsonResponse({'objects': objects})


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
                'username': user.username,
                'email_url': settings.EMAIL_URL
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
            'username': user.username,
            'email_url': settings.EMAIL_URL
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
        user = User.objects.filter(username=username) \
            .annotate(cost_sum=Coalesce(Sum('solved_tasks__cost'), V(0))
                      ) \
            .select_related('organization') \
            .first()

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


class UserTopView(TemplateView):
    template_name = 'users_top.html'

    def get_context_data(self, **kwargs):
        context = super(UserTopView, self).get_context_data(**kwargs)
        page = kwargs.get('page', 1)
        users = User.objects.filter(is_active=True) \
                    .exclude(username='AnonymousUser') \
                    .exclude(groups__name__in=['Administrators']) \
                    .annotate(cost_sum=Coalesce(Sum('solved_tasks__cost'), V(0))) \
                    .order_by('-cost_sum', 'last_solve') \
                    .all()[(page - 1) * settings.USERS_ON_PAGE: page * settings.USERS_ON_PAGE]

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
            'username': username,
            'email_url': settings.EMAIL_URL
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
