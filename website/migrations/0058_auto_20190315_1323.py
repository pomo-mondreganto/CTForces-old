# Generated by Django 2.1.7 on 2019-03-15 10:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0057_auto_20180921_1402'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contest',
            options={'ordering': ('-id',), 'permissions': (('view_unstarted_contest', 'Can view not started contest'), ('can_participate_in_contest', 'Can participate in contest'))},
        ),
    ]