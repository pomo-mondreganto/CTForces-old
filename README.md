# CTForces

This is CTForces legacy version, developed to host jeopardy CTF competitions and provide a platform for tasks upsolving. 

It was created specially for CTF summer camp of [school of programming](https://informatics.ru). 

To run this project, one should start at least one celery worker (they're used in avatar thumbnails rendering and, most importantly, in contest scheduling and rating recalculations).
I personally recommend running in classic environment (gunicorn + nginx).

Rating system is based on [Elo rating system](https://en.wikipedia.org/wiki/Elo_rating_system) and [Codeforces](https://codeforces.com) rating with some modified parameters to provide more dynamic rating changes than ever.

Some vital parameters are expected to be provided in `local_settings.py` right next to `settings.py` in `CTForces` folder. Example of local settings: 


```
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JSON_CONFIG = json.load(open('CTForces/config.json', 'r'))

SECRET_KEY = JSON_CONFIG['SECRET_KEY']

DEBUG = True

ALLOWED_HOSTS = ['*']

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_PASSWORD = JSON_CONFIG['GMAIL_PASSWORD']
EMAIL_HOST_USER = 'ctforces.server@gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'ATOMIC_REQUESTS': True
    }
}

MEDIA_ROOT = 'media'

EMAIL_URL = 'http://127.0.0.1:8080'

INTERNAL_IPS = ['127.0.0.1', 'localhost']
```

`config.json` in the example above contains (try to guess!) `json` with two strings: `SECRET_KEY` and `GMAIL_PASSWORD` &mdash; the app's secret key and gmail password for `EMAIL_HOST_USER` (read more in django docs for mailing).

You are welcome to ask [@pomo_mondreganto](https://telegram.me/pomo_mondreganto) questions about server configuration or backend part of the project and [@xmikasax](https://telegram.me/kekov) about the frontend part (templates, etc...).

Unfortunately, no docker configuration was written for this project and features will not be added per se, but you always can contact us, so the feature may come to life in newer and better CTForces.

Leave your bug reports in the issues, we'll be fixing them while this version is alive at [ctforces.com](https://ctforces.com).
