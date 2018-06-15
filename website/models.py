import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django_countries.fields import CountryField
from mptt.models import TreeForeignKey, MPTTModel
from stdimage.models import StdImageField
from stdimage.validators import MaxSizeValidator

from .models_auxiliary import CustomUploadTo, CustomImageSizeValidator, CustomFileField, stdimage_processor


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
    cost_sum = models.IntegerField(blank=False, default=0)

    country = CountryField(blank_label='(select country)')
    city = models.CharField(max_length=256, blank=True)
    friends = models.ManyToManyField('User', related_name='befriended_by', blank=True, symmetrical=False)

    avatar = StdImageField(
        upload_to=CustomUploadTo(
            upload_type='avatars',
            path='',
            random_filename=True),
        variations={
            'main': (300, 300),
            'small': (100, 100)
        },
        validators=[
            CustomImageSizeValidator(
                min_limit=(150, 150),
                max_limit=(1500, 1500),
                ratio=2
            )
        ],
        default='avatars/default_avatar.png',
        render_variations=stdimage_processor,
        blank=False, null=False
    )

    avatar_processed = models.BooleanField(default=False)

    birth_date = models.DateField(blank=True, null=True)


class Post(models.Model):
    author = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='posts', null=True, blank=True)
    title = models.CharField(max_length=200, blank=False)
    text = models.TextField(blank=False)
    is_important = models.BooleanField(default=False)

    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Post, self).save(*args, **kwargs)


class Comment(MPTTModel):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='comments', null=True, blank=True)
    text = models.TextField(blank=False)
    image = StdImageField(
        upload_to=CustomUploadTo(
            upload_type='images',
            path='',
            random_filename=True
        ),
        render_variations=False,
        validators=[
            MaxSizeValidator(1500, 1500)
        ],
        blank=True, null=True
    )

    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='answers')

    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Comment, self).save(*args, **kwargs)


class Task(models.Model):
    author = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='tasks', blank=True, null=True)
    contest = models.ForeignKey('Contest', on_delete=models.SET_NULL, related_name='tasks', blank=True, null=True)
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(blank=False, null=True)
    flag = models.CharField(max_length=100, null=False, blank=False)

    solved_by = models.ManyToManyField('User', related_name='solved_tasks', blank=True)

    cost = models.IntegerField(null=False, blank=False, default=50)

    is_published = models.BooleanField(default=False)


class Contest(models.Model):
    author = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='contests', blank=True, null=True)
    title = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField(default=datetime.datetime.fromtimestamp(2051222400))
    end_time = models.DateTimeField(default=datetime.datetime.fromtimestamp(2051222500))


class File(models.Model):
    owner = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='files', null=True, blank=True)
    upload_time = models.DateTimeField(editable=False)
    task = models.ForeignKey('Task', on_delete=models.SET_NULL, related_name='files', null=True, blank=True)

    name = models.CharField(max_length=100, null=False, blank=False)

    file_field = CustomFileField(
        upload_to=CustomUploadTo(
            upload_type='files',
            path='',
            append_random=True),
        blank=False, null=False
    )

    def save(self, *args, **kwargs):
        if not self.id:
            self.upload_time = timezone.now()
        super(File, self).save(*args, **kwargs)


class Organization(models.Model):
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)
