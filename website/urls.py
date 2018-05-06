from django.conf.urls import url
from django.urls import path

from .views import UserRegistrationView, UserLoginView, UserInformationView, MainView, test_view, debug_view

urlpatterns = [
    url('^$', MainView.as_view(), name='main_view'),
    url('^signup/$', UserRegistrationView.as_view(), name='signup'),
    url('^signin/', UserLoginView.as_view(), name='signin'),
    path('user/<str:username>', UserInformationView.as_view(), name='user_info'),
    url('^test', test_view, name='test_view'),
    url('^debug', debug_view, name='debug_view'),
]
