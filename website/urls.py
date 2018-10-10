from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from .views import *

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
    path('friends/page/<int:page>/', FriendsView.as_view(), name='friends_view_with_page'),

    re_path('^search_users/$', search_users, name='user_search'),

    path('user/<str:username>/blog/', UserBlogView.as_view(), name='user_blog_view'),
    path('user/<str:username>/blog/page/<int:page>/', UserBlogView.as_view(), name='user_blog_view_with_page'),
    path('user/<str:username>/tasks/', UserTasksView.as_view(), name='user_tasks_view'),
    path('user/<str:username>/tasks/page/<int:page>/', UserTasksView.as_view(), name='user_tasks_view_with_page'),
    path('user/<str:username>/contests/', UserContestListView.as_view(), name='user_contests_view'),
    path('user/<str:username>/contests/page/<int:page>/', UserContestListView.as_view(),
         name='user_contests_view_with_page'),

    path('user/<str:username>/solved_tasks/', UserSolvedTasksView.as_view(),
         name='user_solved_tasks_view'),
    path('user/<str:username>/solved_tasks/page/<int:page>/', UserSolvedTasksView.as_view(),
         name='user_solved_tasks_view_with_page'),

    path('top_users/', UserTopView.as_view(), name='users_top_view'),
    path('top_users/page/<int:page>/', UserTopView.as_view(), name='users_top_view_with_page'),

    path('top_rating_users/', UserRatingTopView.as_view(), name='users_rating_top_view'),
    path('top_rating_users/page/<int:page>/', UserRatingTopView.as_view(), name='users_rating_top_view_with_page'),

    re_path('^add_post/$', PostCreationView.as_view(), name='post_creation_view'),
    path('post/<int:post_id>/', PostView.as_view(), name='post_view'),

    re_path('^leave_comment/$', leave_comment, name='leave_comment'),

    re_path('^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),

    path('task/<int:task_id>/', TaskView.as_view(), name='task_view'),
    path('task/<int:task_id>/edit/', TaskEditView.as_view(), name='task_edit_view'),
    path('task/<int:task_id>/submit/', submit_task, name='task_submit'),
    path('task/<int:task_id>/solved/', TaskSolvedView.as_view(), name='task_solved_view'),
    path('task/<int:task_id>/solved/page/<int:page>/', TaskSolvedView.as_view(), name='task_solved_view_with_page'),

    re_path('^create_task/$', TaskCreationView.as_view(), name='task_creation_view'),

    re_path('^tasks/$', TasksArchiveView.as_view(), name='task_archive_view'),
    path('tasks/page/<int:page>/', TasksArchiveView.as_view(), name='task_archive_view_with_page'),

    re_path('^confirm_email/$', account_confirmation, name='confirm_account'),
    re_path('^resend_email/$', EmailResendView.as_view(), name='resend_email_view'),

    re_path('^password_reset_email/$', PasswordResetEmailView.as_view(), name='password_reset_email'),
    re_path('^reset_password/$', PasswordResetPasswordView.as_view(), name='password_reset_password'),

    re_path('^search_tags/$', search_tags, name='search_tags'),
    re_path('^get_task/$', get_task, name='get_task_by_id'),

    re_path('^create_contest/$', ContestCreationView.as_view(), name='create_contest'),

    path('contests/', ContestsMainListView.as_view(), name='contests_main_list_view'),
    path('contests/page/<int:page>/', ContestsMainListView.as_view(), name='contests_main_list_view_with_page'),

    path('contest/<int:contest_id>/', ContestMainView.as_view(), name='contest_view'),
    path('contest/<int:contest_id>/register/', register_for_contest, name='register_for_contest'),
    path('contest/<int:contest_id>/scoreboard/', ContestScoreboardView.as_view(), name='contest_scoreboard_view'),
    path('contest/<int:contest_id>/task/<int:task_id>/', ContestTaskView.as_view(), name='contest_task_view'),
    path('contest/<int:contest_id>/task/<int:task_id>/submit/', submit_contest_flag, name='contest_task_submit'),

    re_path('^test', test_view, name='test_view'),
    re_path('^debug', debug_view, name='debug_view'),
]
