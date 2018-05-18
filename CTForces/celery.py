import os

import django
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CTForces.settings')
django.setup()

app = Celery('CTForces')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
