from celery import current_app
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models
from django.utils.datetime_safe import datetime
from django_countries.fields import CountryField
from guardian.shortcuts import assign_perm
from mptt.models import TreeForeignKey, MPTTModel
from stdimage.models import StdImageField
from stdimage.validators import MaxSizeValidator

from website.tasks import start_contest, end_contest
from .models_auxiliary import CustomUploadTo, CustomImageSizeValidator, CustomFileField, stdimage_processor


class User(AbstractUser):
    class Meta:
        permissions = (
            ('view_tasks_archive', 'Can view user\'s tasks archive'),
            ('view_contests_archive', 'Can view user\'s contests archive'),
        )

    username_validator = ASCIIUsernameValidator()

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users'
    )

    rank = models.IntegerField(blank=False, default=0)
    rating = models.IntegerField(blank=False, default=2000)
    max_rating = models.IntegerField(blank=False, default=2000)

    country = CountryField(blank_label='(select country)', null=True, blank=True)
    city = models.CharField(max_length=256, blank=True)
    friends = models.ManyToManyField('User', related_name='befriended_by', blank=True, symmetrical=False)

    last_solve = models.DateTimeField(null=True)

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

    birth_date = models.DateField(blank=True, null=True)

    @property
    def is_admin(self):
        return self.is_active and (self.is_staff or self.groups.filter(name='Administrators').exists())

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)
        if self.is_staff:
            if not self.groups.filter(name='Administrators').exists():
                administrators = Group.objects.get(name='Administrators')
                self.groups.add(administrators)
        assign_perm('view_tasks_archive', self, self)
        assign_perm('view_contests_archive', self, self)


class Post(models.Model):
    author = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='posts', null=True, blank=True)
    title = models.CharField(max_length=200, blank=False)
    text = models.TextField(blank=False)
    is_important = models.BooleanField(default=False)

    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.now()
        self.modified = datetime.now()
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
            self.created = datetime.now()
        self.modified = datetime.now()
        return super(Comment, self).save(*args, **kwargs)


class Task(models.Model):
    class Meta:
        permissions = (
            ('view_who_solved_task', 'Can view list of users who solved task'),
        )

    author = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='tasks', blank=True, null=True)
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(blank=False, null=True)
    flag = models.CharField(max_length=100, null=False, blank=False)

    solved_by = models.ManyToManyField('User', related_name='solved_tasks', blank=True)

    cost = models.IntegerField(null=False, blank=False, default=50)

    is_published = models.BooleanField(default=False)
    publication_time = models.DateTimeField(default=datetime.fromtimestamp(1529656118))

    tags = models.ManyToManyField('TaskTag', related_name='tasks', blank=True)

    def save(self, *args, **kwargs):

        if self.id:
            old = Task.objects.only('is_published').get(id=self.id)
            if not old.is_published and self.is_published:
                self.publication_time = datetime.now()
        else:
            if self.is_published:
                self.publication_time = datetime.now()

        super(Task, self).save(*args, **kwargs)


class Contest(models.Model):
    class Meta:
        permissions = (
            ('view_unstarted_contest', 'Can view not started contest'),
            ('can_participate_in_contest', 'Can participate in contest')
        )

    author = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='contests', blank=True, null=True)
    title = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField(default=datetime.fromtimestamp(2051222400))
    end_time = models.DateTimeField(default=datetime.fromtimestamp(2051222500))

    tasks = models.ManyToManyField('Task',
                                   related_name='contests',
                                   blank=True,
                                   through='ContestTaskRelationship')

    participants = models.ManyToManyField('User',
                                          related_name='contests_participated',
                                          blank=True)

    is_published = models.BooleanField(default=False)
    is_running = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    is_registration_open = models.BooleanField(default=False)

    celery_start_task_id = models.CharField(max_length=50, null=True, blank=True)
    celery_end_task_id = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        add_start_task = False
        add_end_task = False

        if self.id:
            old = Contest.objects.only('celery_start_task_id',
                                       'celery_end_task_id',
                                       'start_time',
                                       'end_time').get(id=self.id)

            if old.start_time != self.start_time:
                current_app.control.revoke(old.celery_start_task_id)
                result = start_contest.apply_async(args=(self.id,), eta=self.start_time)
                self.celery_start_task_id = result.id

            if old.end_time != self.end_time:
                current_app.control.revoke(old.celery_end_task_id)
                result = end_contest.apply_async(args=(self.id,), eta=self.end_time)
                self.celery_end_task_id = result.id

        else:
            if self.start_time != datetime.fromtimestamp(2051222400):
                add_start_task = True

            if self.end_time != datetime.fromtimestamp(2051222400):
                add_end_task = True

        super(Contest, self).save(*args, **kwargs)

        if add_start_task:
            result = start_contest.apply_async(args=(self.id,), eta=self.start_time)
            self.celery_start_task_id = result.id
        if add_end_task:
            result = end_contest.apply_async(args=(self.id,), eta=self.end_time)
            self.celery_end_task_id = result.id


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
            self.upload_time = datetime.now()
        super(File, self).save(*args, **kwargs)


class Organization(models.Model):
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)


class TaskTag(models.Model):
    name = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return "Tag object ({}:{})".format(self.id, self.name)


class ContestTaskRelationship(models.Model):
    contest = models.ForeignKey('Contest', on_delete=models.CASCADE, related_name='contest_task_relationship')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='contest_task_relationship')
    solved = models.ManyToManyField('User', related_name='contest_task_relationship', blank=True)
    cost = models.IntegerField(default=0)
    tag = models.ForeignKey('TaskTag', on_delete=models.SET_NULL, related_name='contest_task_relationship',
                            null=True, blank=True)
