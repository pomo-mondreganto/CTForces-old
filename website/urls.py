from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from .views import ContestView
from .views import PasswordResetEmailView, PasswordResetPasswordView
from .views import SettingsGeneralView, SettingsSocialView, FriendsView
from .views import TaskView, TaskCreationView, TasksArchiveView
from .views import UserBlogView, PostCreationView, PostView, leave_comment
from .views import UserRegistrationView, UserLoginView, UserInformationView, MainView, EmailResendView
from .views import UserTasksView
from .views import UserTopView
from .views import activate_email
from .views import logout_user, search_users, submit_task
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
    path('friends/page/<int:page>', FriendsView.as_view(), name='friends_view_with_page'),

    re_path('^search_users/$', search_users, name='user_search'),

    path('user/<str:username>/blog/', UserBlogView.as_view(), name='user_blog_view'),
    path('user/<str:username>/blog/page/<int:page>/', UserBlogView.as_view(), name='user_blog_view_with_page'),

    path('user/<str:username>/tasks/', UserTasksView.as_view(), name='user_tasks_view'),
    path('user/<str:username>/tasks/page/<int:page>/', UserTasksView.as_view(), name='user_tasks_view_with_page'),

    path('top_users/', UserTopView.as_view(), name='users_top_view'),
    path('top_users/page/<int:page>', UserTopView.as_view(), name='users_top_view_with_page'),

    re_path('^add_post/$', PostCreationView.as_view(), name='post_creation_view'),
    path('post/<int:post_id>/', PostView.as_view(), name='post_view'),

    re_path('^leave_comment/$', leave_comment, name='leave_comment'),

    re_path('^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),

    path('task/<int:task_id>/', TaskView.as_view(), name='task_view'),
    path('task/<int:task_id>/submit', submit_task, name='task_submit'),
    re_path('^create_task/$', TaskCreationView.as_view(), name='task_creation_view'),

    re_path('^tasks/$', TasksArchiveView.as_view(), name='task_archive_view'),
    path('tasks/page/<int:page>/', TasksArchiveView.as_view(), name='task_archive_view_with_page'),

    re_path('^confirm_email/$', activate_email, name='confirm_account'),
    re_path('^resend_email/$', EmailResendView.as_view(), name='resend_email_view'),

    re_path('^password_reset_email/$', PasswordResetEmailView.as_view(), name='password_reset_email'),
    re_path('^reset_password/$', PasswordResetPasswordView.as_view(), name='password_reset_password'),

    path('contest/<int:contest_id>/', ContestView.as_view(), name='contest_view'),

    re_path('^test', test_view, name='test_view'),
    re_path('^debug', debug_view, name='debug_view'),
]
