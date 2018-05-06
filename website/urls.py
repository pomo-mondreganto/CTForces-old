from django.urls import path, re_path

from .views import SettingsView, FriendsView
from .views import UserRegistrationView, UserLoginView, UserInformationView, MainView
from .views import logout_view, test_view, debug_view

urlpatterns = [
    re_path('^$', MainView.as_view(), name='main_view'),
    re_path('^signup/$', UserRegistrationView.as_view(), name='signup'),
    re_path('^signin/$', UserLoginView.as_view(), name='signin'),
    re_path('^logout/$', logout_view, name='logout'),
    path('user/<str:username>/', UserInformationView.as_view(), name='user_info'),
    re_path('^settings/$', SettingsView.as_view(), name='settings_view'),
    re_path('^friends/$', FriendsView.as_view(), name='friends_view'),
    re_path('^test', test_view, name='test_view'),
    re_path('^debug', debug_view, name='debug_view'),
]
