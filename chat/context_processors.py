from .models import UserProfile

def active_users(request):
    if request.user.is_authenticated:
        active_users = UserProfile.objects.filter(is_online=True).exclude(user=request.user)
        return {'active_users': active_users}
    return {'active_users': None}
