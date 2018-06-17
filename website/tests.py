from django.contrib.auth import get_user
from django.test import TestCase
from django.urls import reverse

from .models import User


# Create your tests here.


class UserLoginTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', email='test@email.com')
        user.set_password('test_password')
        user.save()

    def test_check_user_can_login(self):
        response = self.client.post(reverse('signin'), {
            'username': 'test',
            'password': 'test_password'
        })
        user = get_user(self.client)
        assert user.is_authenticated

    def test_check_user_can_logout(self):
        response = self.client.post(reverse('signin'), {
            'username': 'test',
            'password': 'test_password'
        })
        user = get_user(self.client)
        response = self.client.get(reverse('logout'))
        user = get_user(self.client)
        assert not user.is_authenticated
