# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.views import LoginView as AuthLoginView
from django.contrib.auth.views import PasswordResetView as AuthPasswordResetView
from django.contrib.auth.views import LogoutView as AuthLogoutView
from .models import Room, Message, UserProfile, FriendRequest, Video, VideoComment, VideoReaction
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

class LoginView(AuthLoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

class HomeView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'chat/home.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return Room.objects.filter(is_private=False)

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
