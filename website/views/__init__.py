from .contests_views import ContestView, UserContestsView
from .others_views import MainView
from .others_views import test_view, debug_view
from .posts_views import UserBlogView, PostCreationView, PostView
from .posts_views import leave_comment
from .tasks_views import TaskView, TaskCreationView, TasksArchiveView
from .tasks_views import UserTasksView, TaskEditView, TaskSolvedView
from .tasks_views import search_tags, submit_task
from .users_views import FriendsView, UserTopView, PasswordResetEmailView
from .users_views import PasswordResetPasswordView
from .users_views import UserInformationView, SettingsGeneralView, SettingsSocialView
from .users_views import UserRegistrationView, EmailResendView, UserLoginView
from .users_views import logout_user, search_users, activate_email
