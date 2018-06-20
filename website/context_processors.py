from django.db.models import Sum, Value as V
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import User, Contest


def top_users(request):
    users = User.objects.filter(is_active=True) \
                .annotate(cost_sum=Coalesce(Sum('solved_tasks__cost'), V(0))) \
                .exclude(username__in=['AnonymousUser', 'admin']) \
                .all().order_by('-cost_sum', 'id')[:10]

    return {'top_users': users}


def current_user_rating(request):
    if request.user.is_authenticated:
        user_rating = User.objects.filter(id=request.user.id) \
            .aggregate(user_rating=Coalesce(Sum('solved_tasks__cost'), V(0)))['user_rating']
        return {'current_user_rating': user_rating}
    return {}


def upcoming_contests(request):
    min_time = timezone.now()
    max_time = min_time + timezone.timedelta(weeks=14)
    contests = Contest.objects.filter(start_time__gt=min_time, start_time__lte=max_time).all()
    return {'upcoming_contests': contests}
