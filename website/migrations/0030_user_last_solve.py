# Generated by Django 2.0.5 on 2018-06-21 14:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0029_auto_20180621_1714'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_solve',
            field=models.DateTimeField(null=True),
        ),
    ]