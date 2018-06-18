from django import forms
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.admin import UserAdmin
from django_mptt_admin.admin import DjangoMpttAdmin
from guardian.admin import GuardedModelAdminMixin

from .models import User, Post, Organization, Comment, Task, Contest


class CustomAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active or not user.is_admin:
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name}
            )


class CustomAdminSite(AdminSite):
    login_form = CustomAdminAuthenticationForm

    def has_permission(self, request):
        return not request.user.is_anonymous and request.user.is_admin


class CustomUserAdmin(GuardedModelAdminMixin, UserAdmin):
    ordering = ('id',)

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Ranking', {
            'fields': ('rank', 'rating', 'max_rating')
        }),
        ('Other info', {
            'fields': ('organization', 'country', 'city', 'avatar')
        }),
        ('Connections', {
            'fields': ('friends',)
        })
    )

    filter_horizontal = ('groups', 'user_permissions', 'friends')

    def __init__(self, model, admin_site):
        self.list_display = ('id',) + UserAdmin.list_display + tuple(field.name for field in model._meta.fields
                                                                     if field.name not in UserAdmin.list_display
                                                                     and field.name != 'id')

        self.list_display_links = ('id', 'username')
        super(CustomUserAdmin, self).__init__(model, admin_site)


class CustomModelAdmin(admin.ModelAdmin):

    def __init__(self, model, admin_site):
        self.list_display = ('id',) + tuple(field.name for field in model._meta.fields if field.name != "id")
        super(CustomModelAdmin, self).__init__(model, admin_site)


class CommentAdmin(DjangoMpttAdmin):

    def __init__(self, model, admin_site):
        self.list_display = ('id',) + tuple(field.name for field in model._meta.fields if field.name != "id")
        super(CommentAdmin, self).__init__(model, admin_site)


custom_admin_site = CustomAdminSite(name='CTForces admin site')

custom_admin_site.register(User, CustomUserAdmin)
custom_admin_site.register(Post, CustomModelAdmin)
custom_admin_site.register(Organization, CustomModelAdmin)
custom_admin_site.register(Comment, CommentAdmin)
custom_admin_site.register(Task, CustomModelAdmin)
custom_admin_site.register(Contest, CustomModelAdmin)
