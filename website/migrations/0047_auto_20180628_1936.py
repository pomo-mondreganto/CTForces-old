# Generated by Django 2.0.5 on 2018-06-28 16:36

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0046_auto_20180628_1804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contesttaskupsolvingrelationship',
            name='solved',
            field=models.ManyToManyField(blank=True, related_name='contest_tasks_upsolving_relationship',
                                         to=settings.AUTH_USER_MODEL),
        ),
    ]