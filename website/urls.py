from django.conf.urls import url

from .views import UserRegistrationView, UserLoginView, MainView, test_view, debug_view

urlpatterns = [
    url('^$', MainView.as_view(), name='main_view'),
    url('^signup/$', UserRegistrationView.as_view(), name='signup'),
    url('^signin/', UserLoginView.as_view(), name='signin'),
    url('^test', test_view, name='test_view'),
    url('^debug', debug_view, name='debug_view'),
]
