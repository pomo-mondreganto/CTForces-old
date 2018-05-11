import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField
from stdimage.models import StdImageField


# Create your models here.

class CustomUploadTo:
    path_pattern = "{path}/{upload_type}"
    file_pattern = "{name}{ext}"

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, instance, filename):
        path, ext = os.path.splitext(filename)
        path, name = os.path.split(path)
        defaults = {
            'ext': ext,
            'name': name,
            'path': path,
            'upload_type': 'other',
        }
        defaults.update(self.kwargs)
        if self.kwargs.get('random_filename'):
            defaults['name'] = uuid.uuid4().hex
        result = os.path.join(self.path_pattern.format(**defaults), self.file_pattern.format(**defaults)).lstrip('/')

        return result

    def deconstruct(self):
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        return path, self.args, self.kwargs


class User(AbstractUser):
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users'
    )

    rank = models.IntegerField(blank=False, default=0)
    rating = models.IntegerField(blank=False, default=1000)
    max_rating = models.IntegerField(blank=False, default=1000)

    country = CountryField(blank_label='(select country)')
    city = models.CharField(max_length=256, blank=True)
    friends = models.ManyToManyField('User', related_name='befriended_by', blank=True, symmetrical=False)

    avatar = StdImageField(upload_to=CustomUploadTo(upload_type='avatars',
                                                    path='',
                                                    random_filename=True
                                                    ),
                           variations={
                               'main': (300, 300),
                               'small': (100, 100)
                           },
                           default='avatars/default_image.jpg', blank=False, null=False)

    birth_date = models.DateField(blank=True, null=True)


class Post(models.Model):
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200, blank=False)
    text = models.TextField(blank=False)
    is_important = models.BooleanField(default=False)


class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(blank=False)


class Organization(models.Model):
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)
