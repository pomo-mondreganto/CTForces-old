from .models import User


def top_users(request):
    users = User.objects.all().order_by('-rating')[:10]
    return {'top_users': users}
