from django.utils import timezone

from .models import User, Contest


def top_users(request):
    users = User.objects.filter(is_active=True) \
                .exclude(username__in=['AnonymousUser', 'admin']) \
                .all().order_by('-cost_sum', 'id')[:10]

    return {'top_users': users}


def upcoming_contests(request):
    min_time = timezone.now()
    max_time = min_time + timezone.timedelta(weeks=14)
    contests = Contest.objects.filter(start_time__gt=min_time, start_time__lte=max_time).all()
    return {'upcoming_contests': contests}
