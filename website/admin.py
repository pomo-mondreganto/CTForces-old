from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Post


# Register your models here.

class CustomUserAdmin(UserAdmin):
    ordering = ('id',)

    def __init__(self, model, admin_site):
        self.list_display = ('id',) + UserAdmin.list_display + tuple(field.name for field in model._meta.fields
                                                                     if field.name not in UserAdmin.list_display
                                                                     and field.name != 'id')
        super(CustomUserAdmin, self).__init__(model, admin_site)


class CustomModelAdmin(admin.ModelAdmin):

    def __init__(self, model, admin_site):
        self.list_display = ('id',) + tuple(field.name for field in model._meta.fields if field.name != "id")
        super(CustomModelAdmin, self).__init__(model, admin_site)


admin.site.register(User, CustomUserAdmin)
admin.site.register(Post, CustomModelAdmin)
