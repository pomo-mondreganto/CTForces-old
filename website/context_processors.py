from django.utils import timezone

from .models import User, Contest


def top_users(request):
    users = User.objects.all().order_by('-rating')[:10]
    return {'top_users': users}


def upcoming_contests(request):
    min_time = timezone.now()
    max_time = min_time + timezone.timedelta(weeks=14)
    contests = Contest.objects.filter(datetime__gt=min_time, datetime__lte=max_time)
    return {'upcoming_contests': contests}
