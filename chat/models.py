from django.db import models
from django.contrib.auth.models import User
import uuid

class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)
    participants = models.ManyToManyField(User, related_name='joined_rooms')

    # New fields for enhanced features
    allow_voice_calls = models.BooleanField(default=True)
    allow_video_calls = models.BooleanField(default=True)
    allow_screen_sharing = models.BooleanField(default=True)
    allow_file_sharing = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    categories = models.CharField(max_length=255, blank=True)  # Stored as comma-separated values

    def __str__(self):
        return self.name

    @property
    def participant_count(self):
        return self.participants.count()

    @property
    def is_active(self):
        return not self.is_archived

class Message(models.Model):
    REACTION_CHOICES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('laugh', '😄'),
        ('sad', '😢'),
        ('angry', '😠'),
        ('wow', '😮')
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    parent_message = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    is_read = models.BooleanField(default=False)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)

    # Message type for different kinds of messages
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('file', 'File Share'),
        ('system', 'System Message'),
        ('code', 'Code Block'),
        ('poll', 'Poll'),
    ]
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')

    # For code blocks
    code_language = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=Message.REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['message', 'user', 'reaction_type']

class RoomInvitation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default-avatar.png')
    bio = models.TextField(max_length=500, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    friends = models.ManyToManyField(User, related_name='friends', blank=True)

    def __str__(self):
        return self.user.username

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('from_user', 'to_user')

class Video(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class VideoComment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class VideoReaction(models.Model):
    REACTION_CHOICES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('laugh', '😄'),
        ('wow', '😮'),
        ('sad', '😢')
    ]

    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('video', 'user')

class PrivateChat(models.Model):
    participants = models.ManyToManyField(User, related_name='private_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    class Meta:
        ordering = ['-last_message_at']

class PrivateMessage(models.Model):
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_private_messages')
    content = models.TextField()
    file = models.FileField(upload_to='private_messages/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

class VoiceCall(models.Model):
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE)
    started_by = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('ongoing', 'Ongoing'),
        ('ended', 'Ended'),
        ('missed', 'Missed')
    ])

# If you want these features in both room chats and private chats:
class Poll(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE, null=True, blank=True)
    private_chat = models.ForeignKey('PrivateChat', on_delete=models.CASCADE, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_multiple_choice = models.BooleanField(default=False)

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)

class PollVote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

class Whiteboard(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE, null=True, blank=True)
    private_chat = models.ForeignKey('PrivateChat', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    data = models.JSONField(default=dict)
