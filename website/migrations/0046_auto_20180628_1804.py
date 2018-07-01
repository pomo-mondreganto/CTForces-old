# Generated by Django 2.0.5 on 2018-06-28 15:04

from django.contrib.auth.management import create_permissions
from django.db import migrations


def migrate_permissions(apps, schema_editor):
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None


def add_unstarted_contest_view_permission_to_admins(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    view_task_perm = Permission.objects.get(codename='view_unstarted_contest')
    administrators = Group.objects.get(name='Administrators')
    administrators.permissions.add(view_task_perm)


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0045_auto_20180628_1804'),
    ]

    operations = [
        migrations.RunPython(migrate_permissions),
        migrations.RunPython(add_unstarted_contest_view_permission_to_admins)
    ]
