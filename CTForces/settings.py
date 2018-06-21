"""
Django settings for CTForces project.

Generated by 'django-admin startproject' using Django 2.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

from CTForces.local_settings import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'website.apps.WebsiteConfig',
    'debug_toolbar',
    'template_profiler_panel',
    'django_countries',
    'stdimage',
    'mptt',
    'django_mptt_admin',
    'guardian'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

ROOT_URLCONF = 'CTForces.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
                'website.context_processors.top_users',
                'website.context_processors.upcoming_contests',
                'website.context_processors.current_user_rating'
            ],
        },
    },
]

WSGI_APPLICATION = 'CTForces.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

AUTH_USER_MODEL = "website.User"

LOGIN_URL = '/signin/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

COUNTRIES_FIRST = ['RU']

POSTS_ON_PAGE = 10
TASKS_ON_PAGE = 20
USERS_ON_PAGE = 30

DEFAULT_AVATAR_MAIN = '/media/avatars/default_avatar.main.png'
DEFAULT_AVATAR_SMALL = '/media/avatars/default_avatar.small.png'

SETTINGS_EXPORT = [
    'POSTS_ON_PAGE',
    'DEFAULT_AVATAR_MAIN',
    'DEFAULT_AVATAR_SMALL'
]

INTERNAL_IPS = ['127.0.0.1', 'localhost']

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'template_profiler_panel.panels.template.TemplateProfilerPanel',
    'djdt_flamegraph.FlamegraphPanel'
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(module)s %(process)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(message)s'
        },
    },
    'handlers': {
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'formatter': 'verbose'
        },
        'file_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/info.log',
            'formatter': 'simple'
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'logs/error.log',
            'formatter': 'verbose'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'email_backend': 'django.core.mail.backends.smtp.EmailBackend',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_debug', 'file_info', 'file_error', 'console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False
        },
        'website': {
            'handlers': ['file_debug', 'file_info', 'file_error', 'console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

FAVICON_PATH = '/static/img/favicon.ico'
APPLE_TOUCH_ICON_PATH = '/static/img/apple-touch-icon.png'
APPLE_TOUCH_ICON_PRECOMPOSED_PATH = '/static/img/apple-touch-icon-precomposed.png'

CELERY_BROKER_URL = 'redis://localhost'
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_IMPORTS = [
    'website.tasks'
]

"""
    2.5MB - 2621440
    5MB - 5242880
    10MB - 10485760
    20MB - 20971520
    50MB - 5242880
    100MB 104857600
    250MB - 214958080
    500MB - 429916160
"""
MAX_FILE_SIZE = 20971520

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.backends.AllowAllUsersModelBackend',
    'guardian.backends.ObjectPermissionBackend'
]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "CTForces"
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

ADMINS = [('Admins', 'ctforces.logs@gmail.com')]
SERVER_EMAIL = 'ctforces.server@gmail.com'
