from django.contrib import admin
from .models import Room, Message, MessageReaction, Task, UserRole, RoomInvitation

admin.site.register(Room)
admin.site.register(Message)
admin.site.register(MessageReaction)
admin.site.register(Task)
admin.site.register(UserRole)
admin.site.register(RoomInvitation)
