from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from .views import SettingsGeneralView, SettingsSocialView, FriendsView
from .views import UserBlogView, PostCreationView, PostView, leave_comment
from .views import UserRegistrationView, UserLoginView, UserInformationView, MainView
from .views import logout_user, search_users
from .views import test_view, debug_view

urlpatterns = [
    re_path('^$', MainView.as_view(), name='main_view'),
    path('page/<int:page>/', MainView.as_view(), name='main_view_with_page'),

    re_path('^signup/$', UserRegistrationView.as_view(), name='signup'),
    re_path('^signin/$', UserLoginView.as_view(), name='signin'),
    re_path('^logout/$', logout_user, name='logout'),

    path('user/<str:username>/', UserInformationView.as_view(), name='user_info'),

    re_path('^settings/general/$', SettingsGeneralView.as_view(), name='settings_general_view'),
    re_path('^settings/social/$', SettingsSocialView.as_view(), name='settings_social_view'),

    re_path('^friends/$', FriendsView.as_view(), name='friends_view'),

    re_path('^search_users/$', search_users, name='user_search'),

    path('user/<str:username>/blog/', UserBlogView.as_view(), name='user_blog_view'),
    path('user/<str:username>/blog/page/<int:page>/', UserBlogView.as_view(), name='user_blog_view_with_page'),

    re_path('^add_post/$', PostCreationView.as_view(), name='post_creation_view'),
    path('post/<int:post_id>/', PostView.as_view(), name='post_view'),

    re_path('^leave_comment/$', leave_comment, name='leave_comment'),

    re_path('^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),

    re_path('^test', test_view, name='test_view'),
    re_path('^debug', debug_view, name='debug_view'),
]
