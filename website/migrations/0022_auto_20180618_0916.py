# Generated by Django 2.0.5 on 2018-06-18 06:16

import django_countries.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0021_auto_20180617_1540'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='country',
            field=django_countries.fields.CountryField(max_length=2, null=True),
        ),
    ]
