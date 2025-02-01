from django.utils import timezone
from .models import UserProfile

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            UserProfile.objects.filter(user=request.user).update(
                last_activity=timezone.now(),
                is_online=True
            )
        response = self.get_response(request)
        return response
