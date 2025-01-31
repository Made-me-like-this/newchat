from django.contrib import admin
from .models import Room

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'is_private', 'is_archived')
    list_filter = ('is_private', 'is_archived', 'allow_voice_calls', 'allow_video_calls')
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('created_at',)
    filter_horizontal = ('participants',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'created_by', 'participants')
        }),
        ('Settings', {
            'fields': ('is_private', 'is_archived', 'categories')
        }),
        ('Features', {
            'fields': ('allow_voice_calls', 'allow_video_calls', 'allow_screen_sharing', 'allow_file_sharing')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
