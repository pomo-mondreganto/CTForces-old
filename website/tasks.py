from celery import shared_task
from django.apps import apps
from stdimage.utils import render_variations

get_model = apps.get_model


@shared_task
def process_stdimage(file_name, variations, storage):
    render_variations(file_name, variations, replace=True, storage=storage)
    obj = get_model('website', 'User').objects.get(avatar=file_name)
    obj.save()


@shared_task
def start_contest(contest_id):
    print('Starting contest {}'.format(contest_id))
    contest = get_model('website', 'Contest').objects.filter(id=contest_id).first()

    if not contest:
        print('Contest not staring, no such contest')
        return

    contest.is_running = True
    contest.save()


@shared_task
def end_contest(contest_id):
    print('Ending contest {}'.format(contest_id))
    contest = get_model('website', 'Contest').objects.filter(id=contest_id).first()
    if not contest:
        print('Contest not ending, no such contest')
        return

    contest.is_running = False
    contest.is_finished = True
    contest.save()
