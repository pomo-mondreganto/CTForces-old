from django.conf.urls import url

from .views import UserRegistrationView, MainView

urlpatterns = [
    url('^$', MainView.as_view(), name='main_view'),
    url('^signup/$', UserRegistrationView.as_view(), name='register')
]
