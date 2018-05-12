from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django_mptt_admin.admin import DjangoMpttAdmin

from .models import User, Post, Organization, Comment


# Register your models here.

class CustomUserAdmin(UserAdmin):
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


admin.site.register(User, CustomUserAdmin)
admin.site.register(Post, CustomModelAdmin)
admin.site.register(Organization, CustomModelAdmin)
admin.site.register(Comment, CommentAdmin)
