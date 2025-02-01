# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.views import LoginView as AuthLoginView
from django.contrib.auth.views import PasswordResetView as AuthPasswordResetView
from django.contrib.auth.views import LogoutView as AuthLogoutView
from .models import Room, Message, UserProfile, FriendRequest, Video, VideoComment, VideoReaction, MessageReaction, PrivateChat, PrivateMessage
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import UserRegistrationForm, RoomForm, UserProfileForm, VideoUploadForm
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import Count
from django.template.defaultfilters import timesince
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import json

class LoginView(AuthLoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Login successful!")  # Success message for toast
        return response

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")  # Logout success message for toast
        return redirect('login')

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Registration successful! You can now log in.")  # Success message for toast
        return response


@login_required
def home(request):
    rooms = Room.objects.filter(is_archived=False)
    active_users = UserProfile.objects.filter(user__is_active=True)

    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        rooms = rooms.filter(name__icontains=search_query)

    # Apply category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        rooms = rooms.filter(categories__icontains=category_filter)

    # Apply other filters
    if request.GET.get('private'):
        rooms = rooms.filter(is_private=True)
    if request.GET.get('active'):
        rooms = rooms.filter(is_active=True)
    if request.GET.get('my_rooms') and request.user.is_authenticated:
        rooms = rooms.filter(created_by=request.user)

    # Sorting functionality
    sort_by = request.GET.get('sort', '')
    if sort_by == 'newest':
        rooms = rooms.order_by('-created_at')
    elif sort_by == 'popular':
        rooms = rooms.order_by('-num_members')  # Replace num_members with the actual popularity metric
    elif sort_by == 'alphabetical':
        rooms = rooms.order_by('name')

    # Get unique categories from all rooms
    all_categories = set()
    for room in rooms:
        if room.categories:
            categories = [cat.strip() for cat in room.categories.split(',')]
            all_categories.update(categories)

    # Create category objects with room counts
    categories = []
    for category in all_categories:
        room_count = Room.objects.filter(
            categories__icontains=category,
            is_archived=False
        ).count()
        categories.append({
            'name': category,
            'slug': category.lower().replace(' ', '-'),
            'room_count': room_count
        })

    context = {
        'rooms': rooms,
        'active_users': active_users,
        'categories': sorted(categories, key=lambda x: x['name']),
        'search_query': search_query,
        'selected_category': category_filter,
        'sort_by': sort_by
    }

    return render(request, 'chat/home.html', context)

class RoomView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = 'chat/chat_room.html'
    context_object_name = 'room'
    pk_url_kwarg = 'room_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.messages.all()
        return context

class CreateRoomView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'chat/create_room.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.object.participants.add(self.request.user)
        return response

class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'chat/message_list.html'
    context_object_name = 'messages'

    def get_queryset(self):
        room = get_object_or_404(Room, id=self.kwargs['room_id'])
        return Message.objects.filter(room=room)

class ProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'chat/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.userprofile

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'chat/edit_profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user.userprofile

class VideoListView(LoginRequiredMixin, ListView):
    model = Video
    template_name = 'video/video_list.html'
    context_object_name = 'videos'

class VideoUploadView(LoginRequiredMixin, CreateView):
    model = Video
    form_class = VideoUploadForm
    template_name = 'video/video_upload.html'
    success_url = reverse_lazy('video_list')

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'video/video_detail.html'
    context_object_name = 'video'
    pk_url_kwarg = 'video_id'

    def get(self, request, *args, **kwargs):
        video = self.get_object()
        video.views += 1
        video.save()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prev_video'] = Video.objects.filter(id__lt=self.object.id).order_by('-id').first()
        context['next_video'] = Video.objects.filter(id__gt=self.object.id).order_by('id').first()

        context['reaction_choices'] = VideoReaction.REACTION_CHOICES
        context['reaction_counts'] = self.object.reactions.values('reaction_type').annotate(count=Count('id'))
        if self.request.user.is_authenticated:
            user_reaction = self.object.reactions.filter(user=self.request.user).first()
            context['user_reaction'] = user_reaction.reaction_type if user_reaction else None

        return context

class FriendListView(LoginRequiredMixin, ListView):
    template_name = 'chat/friend_list.html'
    context_object_name = 'friends'

    def get_queryset(self):
        return self.request.user.userprofile.friends.all()

class SendFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, user_id):
        to_user = get_object_or_404(User, id=user_id)

        # Ensure a friend request is not sent again if it already exists
        if FriendRequest.objects.filter(from_user=request.user, to_user=to_user, status=FriendRequest.PENDING).exists():
            return JsonResponse({'status': 'already_pending'})

        FriendRequest.objects.get_or_create(
            from_user=request.user,
            to_user=to_user,
            defaults={'status': FriendRequest.PENDING}
        )
        return JsonResponse({'status': 'success'})

class AcceptFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, request_id):
        friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
        friend_request.status = FriendRequest.ACCEPTED
        friend_request.save()

        # Add users to each other's friends list
        request.user.userprofile.friends.add(friend_request.from_user)
        friend_request.from_user.userprofile.friends.add(request.user)

        return JsonResponse({'status': 'success'})

class ActiveUsersView(LoginRequiredMixin, View):
    def get(self, request):
        active_users = UserProfile.objects.filter(is_online=True).values('user__username', 'last_activity')
        return JsonResponse({'active_users': list(active_users)})

class PasswordResetView(AuthPasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

class VideoCommentView(APIView):
    def post(self, request, video_id):
        # Ensure video exists
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return Response({"error": "Video not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create comment
        content = request.data.get("content")
        if not content:
            return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)

        comment = VideoComment.objects.create(
            video=video,
            user=request.user,
            content=content
        )

        # Return the comment data in the response
        return Response({
            "success": True,
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "comment_user": comment.user.username,
            "comment_user_avatar": comment.user.userprofile.avatar.url if comment.user.userprofile.avatar else None,
            "comment_time_ago": timesince(comment.created_at) + " ago",  # Format time
        }, status=status.HTTP_201_CREATED)

class VideoReactionView(APIView):
    def post(self, request, video_id):
        # Ensure video exists
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return Response({"error": "Video not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get the reaction type
        reaction_type = request.data.get("reaction_type")
        if reaction_type not in dict(VideoReaction.REACTION_CHOICES):
            return Response({"error": "Invalid reaction type"}, status=status.HTTP_400_BAD_REQUEST)

        # Create reaction
        reaction, created = VideoReaction.objects.get_or_create(
            video=video,
            user=request.user,
            defaults={"reaction_type": reaction_type}
        )

        if not created:
            # If reaction exists, update it
            reaction.reaction_type = reaction_type
            reaction.save()

        return Response({
            "reaction_type": reaction.reaction_type,
            "created_at": reaction.created_at
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    # Check if user has permission to delete
    if request.user != message.user and request.user != message.room.created_by:
        raise PermissionDenied("You don't have permission to delete this message")

    message.delete()
    return JsonResponse({'status': 'success'})

@login_required
def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # Ensure the user is the creator of the room
    if room.created_by == request.user:
        room.delete()
        return JsonResponse({'status': 'success'}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': 'You are not authorized to delete this room.'}, status=403)

@login_required
def add_message(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        file = request.FILES.get('file')

        if not message_text and not file:
            return JsonResponse({'error': 'Message or file is required'}, status=400)

        message = Message.objects.create(
            room=room,
            user=request.user,
            content=message_text
        )

        if file:
            message.file = file
            message.file_name = file.name
            message.save()

        # Send WebSocket message
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type': 'chat_message',
                'message': message_text,
                'user_id': str(request.user.id),
                'username': request.user.username,
                'file_url': message.file.url if file else None,
                'file_name': message.file_name if file else None
            }
        )

        return JsonResponse({'status': 'success'})

@login_required
def add_reaction(request, message_id):
    if request.method == 'POST':
        message = get_object_or_404(Message, id=message_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')

        if reaction_type not in dict(MessageReaction.REACTION_CHOICES):
            return JsonResponse({'error': 'Invalid reaction type'}, status=400)

        # Remove existing reaction if any
        MessageReaction.objects.filter(
            message=message,
            user=request.user
        ).delete()

        # Add new reaction
        reaction = MessageReaction.objects.create(
            message=message,
            user=request.user,
            reaction_type=reaction_type
        )

        return JsonResponse({
            'status': 'success',
            'reaction': {
                'type': reaction.reaction_type,
                'display': reaction.get_reaction_type_display()
            }
        })

@login_required
def private_chats_list(request):
    chats = PrivateChat.objects.filter(participants=request.user)
    return render(request, 'chat/private_chats_list.html', {'chats': chats})

@login_required
def private_chat_room(request, chat_id):
    chat = get_object_or_404(PrivateChat, id=chat_id, participants=request.user)
    messages = chat.messages.all()
    other_user = chat.get_other_participant(request.user)

    # Mark unread messages as read
    messages.filter(sender=other_user, is_read=False).update(is_read=True)

    return render(request, 'chat/private_chat_room.html', {
        'chat': chat,
        'messages': messages,
        'other_user': other_user
    })

@login_required
def create_private_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    # Check if chat already exists
    chat = PrivateChat.objects.filter(participants=request.user)\
        .filter(participants=other_user).first()

    if not chat:
        chat = PrivateChat.objects.create()
        chat.participants.add(request.user, other_user)

    return JsonResponse({'chat_id': chat.id})

@login_required
def room_settings(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == 'POST':
        room.name = request.POST['name']
        room.description = request.POST['description']
        room.categories = request.POST['categories']
        room.save()
        return redirect('home')

    return render(request, 'chat/room_settings.html', {'room': room})

@login_required
def invite_users(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # Implement logic for inviting users to the room
    if request.method == 'POST':
        # Logic for inviting users
        pass

    return render(request, 'chat/invite_users.html', {'room': room})

@login_required
def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == 'POST' and room.created_by == request.user:
        room.delete()
        return redirect('home')  # Redirect to home or room list

    return render(request, 'chat/confirm_delete.html', {'room': room})

@login_required
def update_room_settings(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # Check if the user has permission to edit the room settings (e.g., is the creator?)
    if room.created_by != request.user:
        return redirect('home')  # Or show an error if the user is not authorized

    if request.method == 'POST':
        # Here, you can add the logic to handle the settings update form submission
        room.name = request.POST.get('name')
        room.description = request.POST.get('description')
        # Handle other settings updates as needed
        room.save()

        return redirect('room_detail', room_id=room.id)  # Redirect to room details or somewhere else

    return render(request, 'chat/room_settings.html', {'room': room})


@login_required
@require_http_methods(["POST"])
def toggle_task(request, task_id):
    """Toggle task completion status."""
    task = get_object_or_404(Task, id=task_id)

    # Check if user has permission to modify task
    if not (request.user == task.assigned_to or request.user == task.room.created_by):
        raise PermissionDenied("You don't have permission to modify this task.")

    task.completed = not task.completed
    task.save()

    return JsonResponse({
        'success': True,
        'task_id': task.id,
        'completed': task.completed
    })

@login_required
def room_tasks(request, room_id):
    """Get all tasks for a room."""
    room = get_object_or_404(Room, id=room_id)
    if not room.participants.filter(id=request.user.id).exists():
        raise PermissionDenied("You are not a participant in this room.")

    tasks = Task.objects.filter(room=room).select_related('assigned_to').order_by('-created_at')

    return JsonResponse([{
        'id': task.id,
        'description': task.description,
        'completed': task.completed,
        'assigned_to': {
            'id': task.assigned_to.id,
            'username': task.assigned_to.username
        },
        'created_at': task.created_at.isoformat()
    } for task in tasks], safe=False)

@login_required
@require_http_methods(["POST", "DELETE"])
def message_reactions(request, message_id):
    """Handle adding/removing reactions to messages."""
    message = get_object_or_404(Message, id=message_id)

    if request.method == "POST":
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')

        # Remove existing reaction of same type by this user
        Reaction.objects.filter(
            message=message,
            user=request.user,
            reaction_type=reaction_type
        ).delete()

        # Add new reaction
        reaction = Reaction.objects.create(
            message=message,
            user=request.user,
            reaction_type=reaction_type
        )

        return JsonResponse({
            'success': True,
            'reaction_id': reaction.id
        })

    elif request.method == "DELETE":
        Reaction.objects.filter(
            message=message,
            user=request.user
        ).delete()

        return JsonResponse({'success': True})

@login_required
@require_http_methods(["POST"])
def message_reply(request, message_id):
    """Add a reply to a message."""
    parent_message = get_object_or_404(Message, id=message_id)
    data = json.loads(request.body)

    reply = Message.objects.create(
        room=parent_message.room,
        user=request.user,
        content=data.get('content'),
        parent_message=parent_message,
        message_type='reply'
    )

    return JsonResponse({
        'success': True,
        'reply': {
            'id': reply.id,
            'content': reply.content,
            'user': {
                'id': reply.user.id,
                'username': reply.user.username
            },
            'timestamp': reply.timestamp.isoformat()
        }
    })

@login_required
@require_http_methods(["PUT"])
def edit_message(request, message_id):
    """Edit a message."""
    message = get_object_or_404(Message, id=message_id)

    if message.user != request.user:
        raise PermissionDenied("You can only edit your own messages.")

    data = json.loads(request.body)
    message.content = data.get('content')
    message.edited = True
    message.save()

    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'edited': message.edited
        }
    })

@login_required
@require_http_methods(["DELETE"])
def delete_message(request, message_id):
    """Delete a message."""
    message = get_object_or_404(Message, id=message_id)

    if not (message.user == request.user or request.user.is_staff):
        raise PermissionDenied("You don't have permission to delete this message.")

    message.delete()
    return JsonResponse({'success': True})

@login_required
def room_participants(request, room_id):
    """Get list of room participants."""
    room = get_object_or_404(Room, id=room_id)
    if not room.participants.filter(id=request.user.id).exists():
        raise PermissionDenied("You are not a participant in this room.")

    participants = room.participants.all().select_related('profile')

    return JsonResponse([{
        'id': participant.id,
        'username': participant.username,
        'avatar_url': participant.profile.avatar.url if participant.profile.avatar else None,
        'role': UserRole.objects.filter(user=participant, room=room).first().role if UserRole.objects.filter(user=participant, room=room).exists() else 'member'
    } for participant in participants], safe=False)

@login_required
@require_http_methods(["POST"])
def change_participant_role(request, room_id, user_id):
    """Change a participant's role."""
    room = get_object_or_404(Room, id=room_id)
    target_user = get_object_or_404(room.participants, id=user_id)

    # Check if requester has permission to change roles
    requester_role = UserRole.objects.filter(user=request.user, room=room).first()
    if not requester_role or requester_role.role not in ['admin', 'moderator']:
        raise PermissionDenied("You don't have permission to change roles.")

    data = json.loads(request.body)
    new_role = data.get('role')

    if new_role not in ['admin', 'moderator', 'member']:
        return JsonResponse({'error': 'Invalid role'}, status=400)

    user_role, created = UserRole.objects.get_or_create(
        user=target_user,
        room=room,
        defaults={'role': new_role}
    )

    if not created:
        user_role.role = new_role
        user_role.save()

    return JsonResponse({
        'success': True,
        'user_id': target_user.id,
        'new_role': new_role
    })

@login_required
@require_http_methods(["POST"])
def moderate_participant(request, room_id, user_id):
    """Moderate user actions (mute/kick/ban)."""
    room = get_object_or_404(Room, id=room_id)
    target_user = get_object_or_404(room.participants, id=user_id)

    # Check if requester has permission to moderate
    requester_role = UserRole.objects.filter(user=request.user, room=room).first()
    if not requester_role or requester_role.role not in ['admin', 'moderator']:
        raise PermissionDenied("You don't have permission to moderate users.")

    data = json.loads(request.body)
    action = data.get('action')

    if action not in ['mute', 'kick', 'ban']:
        return JsonResponse({'error': 'Invalid action'}, status=400)

    if action == 'mute':
        # Implementation for muting user
        room.muted_users.add(target_user)
    elif action == 'kick':
        # Implementation for kicking user
        room.participants.remove(target_user)
    elif action == 'ban':
        # Implementation for banning user
        room.banned_users.add(target_user)
        room.participants.remove(target_user)

    return JsonResponse({
        'success': True,
        'user_id': target_user.id,
        'action': action
    })
