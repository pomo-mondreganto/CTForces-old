from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField


# Create your models here.

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

    country = CountryField(blank_label='(undefined)', blank=True)
    city = models.CharField(max_length=256, blank=True)
    friends = models.ManyToManyField('User', related_name='befriended_by', blank=True, symmetrical=False)

    avatar = models.ImageField(blank=True, upload_to=settings.AVATAR_UPLOAD_DIR)

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
