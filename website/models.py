import os
import uuid
from io import BytesIO

from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
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


class CustomImageSizeValidator:

    def __init__(self, min_limit, max_limit, ratio):
        self.min_limit = min_limit
        self.max_limit = max_limit
        self.ratio_limit = ratio

    @staticmethod
    def clean(value):
        value.seek(0)
        stream = BytesIO(value.read())
        img = Image.open(stream)
        return img.size

    def __call__(self, value):
        cleaned = self.clean(value)
        if self.compare_min(cleaned, self.min_limit):
            params = {
                'width': self.min_limit[0],
                'height': self.min_limit[1],
            }
            raise ValidationError('''Your image is too small. 
                                     The minimal resolution is {width}x{height}'''.format(**params),
                                  code='min_resolution')
        if self.compare_max(cleaned, self.max_limit):
            params = {
                'width': self.max_limit[0],
                'height': self.max_limit[1],
            }
            raise ValidationError('''Your image is too big. 
                                     The maximal resolution is {width}x{height}'''.format(**params),
                                  code='max_resolution')

        if self.compare_ratio(cleaned, self.ratio_limit):
            params = {
                'ratio': self.ratio_limit,
            }
            raise ValidationError('''Your image is too unbalanced. 
                                     The maximal ratio is {ratio}'''.format(**params),
                                  code='ratio')

    @staticmethod
    def compare_min(img_size, min_size):
        return img_size[0] < min_size[0] or img_size[1] < min_size[1]

    @staticmethod
    def compare_max(img_size, max_size):
        return img_size[0] > max_size[0] or img_size[1] > max_size[1]

    @staticmethod
    def compare_ratio(img_size, ratio):
        return img_size[0] * ratio <= img_size[1] or img_size[1] * ratio <= img_size[0]


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
                           validators=[CustomImageSizeValidator(min_limit=(150, 150),
                                                                max_limit=(1500, 1500),
                                                                ratio=2)],
                           default='avatars/default_image.jpg',
                           blank=False, null=False)

    birth_date = models.DateField(blank=True, null=True)


class Post(models.Model):
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200, blank=False)
    text = models.TextField(blank=False)
    is_important = models.BooleanField(default=False)

    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.edited = timezone.now()
        return super(Post, self).save(*args, **kwargs)


class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(blank=False)

    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.edited = timezone.now()
        return super(Comment, self).save(*args, **kwargs)


class Organization(models.Model):
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)
