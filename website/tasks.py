from celery import shared_task
from django.apps import apps
from stdimage.utils import render_variations

get_model = apps.get_model


@shared_task
def process_stdimage(file_name, variations, storage):
    render_variations(file_name, variations, replace=True, storage=storage)
    obj = get_model('website', 'User').objects.get(avatar=file_name)
    obj.avatar_processed = True
    obj.save()


@shared_task
def start_contest(contest_id):
    print('Starting contest {}'.format(contest_id))


@shared_task
def end_contest(contest_id):
    print('Ending contest {}'.format(contest_id))
