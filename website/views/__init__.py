from .contests_views import ContestView, UserContestsView
from .others_views import MainView
from .others_views import test_view, debug_view
from .posts_views import UserBlogView, PostCreationView, PostView
from .posts_views import leave_comment
from .tasks_views import TaskView, TaskCreationView, TasksArchiveView
from .tasks_views import UserTasksView, TaskEditView, TaskSolvedView
from .tasks_views import search_tags, submit_task
from .user_views import FriendsView, UserTopView, PasswordResetEmailView
from .user_views import PasswordResetPasswordView
from .user_views import UserInformationView, SettingsGeneralView, SettingsSocialView
from .user_views import UserRegistrationView, EmailResendView, UserLoginView
from .user_views import logout_user, search_users, activate_email
