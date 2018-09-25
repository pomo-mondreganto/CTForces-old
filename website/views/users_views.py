from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import SetPasswordForm
from django.core.mail import send_mail
from django.db.models import Sum, Value as V
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from website.forms import RegistrationForm
from website.forms import UserGeneralUpdateForm, UserSocialUpdateForm
from website.mixins import CustomLoginRequiredMixin as LoginRequiredMixin
from website.models import User
from website.tokens import deserialize, serialize
from .view_classes import GetPostTemplateViewWithAjax, PagedTemplateView


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
def account_confirmation(request):
    token = request.GET.get('token')
    user_id = deserialize(token, 'email_confirmation', max_age=86400)

    if user_id is None:
        messages.error(request=request, message='Token is invalid or expired')
        return render(request=request, template_name='account_events_templates/account_confirmation.html')

    user = User.objects.filter(id=user_id).first()

    if not user:
        messages.error(request=request, message='Account does not exist.')
        return render(request=request, template_name='account_events_templates/account_confirmation.html')

    if not user.is_active:
        messages.success(request=request, message='Account confirmed.')
        user.is_active = True
        user.save()
    else:
        messages.success(request=request, message='Account has already been confirmed.')

    return render(request=request, template_name='account_events_templates/account_confirmation.html')


class UserRegistrationView(GetPostTemplateViewWithAjax):
    template_name = 'index_templates/registration.html'

    def handle_ajax(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST)

        result = dict()

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

            result['message'] = 'User successfully registered! " \
                                             "Follow the link in your email to confirm your account!'
            result['success'] = True
            result['next'] = reverse('signin')
        else:
            print(form.errors)

            result['success'] = False
            result['errors'] = form.errors

        return JsonResponse(result)


class EmailResendView(GetPostTemplateViewWithAjax):
    template_name = 'account_events_templates/resend_email.html'

    def handle_ajax(self, request, *args, **kwargs):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        result = dict()

        if not user:
            result['success'] = False
            result['errors'] = dict(email='User with this email is not registered.')
            return JsonResponse(result)

        if user.is_active:
            result['success'] = False
            result['errors'] = dict(email='Account already activated.')
            return JsonResponse(result)

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

        result['success'] = True
        result['next'] = reverse('signin')

        return JsonResponse(result)


class UserLoginView(GetPostTemplateViewWithAjax):
    template_name = 'index_templates/login.html'

    def handle_ajax(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request=request, username=username, password=password)

        result = dict()

        if not user:
            result['success'] = False
            result['errors'] = dict(password='Credentials are invalid')
            return JsonResponse(result)

        elif not user.is_active:
            result['success'] = False
            result['errors'] = dict(not_activated='Account is not activated')
            return JsonResponse(result)

        login(request, user)

        result['success'] = True

        next_page = request.GET.get('next')
        if not next_page:
            next_page = reverse('main_view')

        result['next'] = next_page

        return JsonResponse(result)


class UserInformationView(TemplateView):
    template_name = 'profile_templates/profile.html'

    def get_context_data(self, **kwargs):
        context = super(UserInformationView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        user = User.objects.filter(
            username=username
        ).annotate(
            cost_sum=
            Coalesce(
                Sum(
                    'solved_tasks__cost'
                ),
                V(0)
            )
        ).select_related(
            'organization'
        ).first()

        if not user:
            raise Http404()

        context['user'] = user
        return context


class SettingsGeneralView(LoginRequiredMixin, GetPostTemplateViewWithAjax):
    template_name = 'profile_templates/settings_general.html'

    def handle_ajax(self, request, *args, **kwargs):
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
    template_name = 'profile_templates/settings_social.html'

    def handle_ajax(self, request, *args, **kwargs):
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


class FriendsView(LoginRequiredMixin, GetPostTemplateViewWithAjax, PagedTemplateView):
    template_name = 'profile_templates/friends.html'

    def get_context_data(self, **kwargs):
        context = super(FriendsView, self).get_context_data(**kwargs)
        page = context['page']

        friends = self.request.user.friends.all()[(page - 1) * settings.USERS_ON_PAGE: page * settings.USERS_ON_PAGE]
        context['friends'] = friends

        page_count = (self.request.user.friends.count() + settings.USERS_ON_PAGE - 1) // settings.USERS_ON_PAGE
        context['page_count'] = page_count

        return context

    def handle_ajax(self, request, *args, **kwargs):
        friend_id = request.POST.get('friend_id')
        add = request.POST.get('add', 'true') == 'true'

        result = dict()

        if not friend_id:
            result['success'] = False
            result['errors'] = dict(friend_id='friend_id not provided')
            return JsonResponse(result)

        try:
            friend_id = int(friend_id)
        except ValueError:
            result['success'] = False
            result['errors'] = dict(friend_id='Invalid friend_id')
            return JsonResponse(result)

        friend = User.objects.filter(id=friend_id).first()
        if not friend:
            result['success'] = False
            result['errors'] = dict(friend_id='No user with such id')
            return JsonResponse(result)

        if add:
            request.user.friends.add(friend)
        else:
            request.user.friends.remove(friend)

        request.user.save()
        result['success'] = True
        return JsonResponse(result)


class UserTopView(PagedTemplateView):
    template_name = 'index_templates/users_top.html'

    def get_context_data(self, **kwargs):
        context = super(UserTopView, self).get_context_data(**kwargs)
        page = context['page']

        qs = User.objects.filter(
            is_active=True
        ).exclude(
            username='AnonymousUser'
        ).exclude(
            groups__name='Administrators'
        )

        users = qs.annotate(
            cost_sum=Coalesce(
                Sum(
                    'solved_tasks__cost'
                ),
                V(0)
            )
        ).order_by(
            '-cost_sum',
            'last_solve',
            'id'
        ).all()[(page - 1) * settings.USERS_ON_PAGE: page * settings.USERS_ON_PAGE]

        page_count = (qs.count() + settings.USERS_ON_PAGE - 1) // settings.USERS_ON_PAGE

        start_number = (page - 1) * settings.USERS_ON_PAGE

        context['start_number'] = start_number
        context['users'] = users
        context['page_count'] = page_count

        return context


class PasswordResetEmailView(GetPostTemplateViewWithAjax):
    template_name = 'account_events_templates/reset_password_email.html'

    def handle_ajax(self, request, *args, **kwargs):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        result = dict()

        if not user:
            result['success'] = False
            result['errors'] = dict(email='No user with such email exists')
            return JsonResponse(result)

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
        result['success'] = True
        result['message'] = 'Follow the link in your email to reset your password!'
        result['next'] = reverse('signin')
        return JsonResponse(result)


class PasswordResetPasswordView(GetPostTemplateViewWithAjax):
    template_name = 'account_events_templates/reset_password_password.html'

    def get_context_data(self, **kwargs):
        context = super(PasswordResetPasswordView, self).get_context_data(**kwargs)
        context['token'] = self.request.GET.get('token')
        return context

    def handle_default(self, request, *args, **kwargs):
        token = request.POST.get('token')
        user_id = deserialize(token, 'password_reset', max_age=86400)

        if user_id is None:
            messages.error(request=request, message='Token is invalid or expired')
            return render(request=request, template_name='account_events_templates/reset_password_endpoint.html')

        user = User.objects.filter(id=user_id).first()

        if not user:
            messages.error(request=request, message='Account does not exist.')
            return render(request=request, template_name='account_events_templates/reset_password_endpoint.html')
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request=request, message='Password was reset successfully!')
            return render(request=request, template_name='account_events_templates/reset_password_endpoint.html')
        else:
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)

            response = redirect('password_reset_password')

            if request.POST.get('token'):
                response['Location'] += '?token={}'.format(request.POST.get('token'))

            return response
