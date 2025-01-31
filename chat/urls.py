from django.urls import path
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from .views import (
    LoginView, LogoutView, RegisterView, RoomView, CreateRoomView,
    MessageListView, ProfileView, ProfileEditView, VideoListView, VideoUploadView,
    VideoDetailView, FriendListView, SendFriendRequestView, AcceptFriendRequestView,
    ActiveUsersView, VideoCommentView, VideoReactionView
)
from . import views

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('room/<uuid:room_id>/', RoomView.as_view(), name='room_detail'),
    path('room/create/', CreateRoomView.as_view(), name='create_room'),
    path('room/<int:room_id>/messages/', MessageListView.as_view(), name='message_list'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='edit_profile'),
    path('videos/', VideoListView.as_view(), name='video_list'),
    path('videos/upload/', VideoUploadView.as_view(), name='video_upload'),
    path('videos/<int:video_id>/', VideoDetailView.as_view(), name='video_detail'),
    path('videos/<int:video_id>/comment/', VideoCommentView.as_view(), name='video_comment'),
    path('videos/<int:video_id>/react/', VideoReactionView.as_view(), name='video_reaction'),
    path('friends/', FriendListView.as_view(), name='friend_list'),
    path('friend-request/send/<int:user_id>/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('friend-request/accept/<int:request_id>/', AcceptFriendRequestView.as_view(), name='accept_friend_request'),
    path('active-users/', ActiveUsersView.as_view(), name='active_users'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('api/messages/<int:message_id>/', views.delete_message, name='delete_message'),
    path('api/rooms/<uuid:room_id>/', views.delete_room, name='delete_room'),
    path('api/rooms/<uuid:room_id>/messages/', views.add_message, name='add_message'),
    path('api/messages/<int:message_id>/reactions/', views.add_reaction, name='add_reaction'),
    path('private-chats/', views.private_chats_list, name='private_chats_list'),
    path('private-chat/<int:chat_id>/', views.private_chat_room, name='private_chat_room'),
    path('create-private-chat/<int:user_id>/', views.create_private_chat, name='create_private_chat'),
    path('delete-room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('room-settings/<uuid:room_id>/', views.room_settings, name='room_settings'),
     path('rooms/<uuid:room_id>/settings/', views.update_room_settings, name='update_room_settings'),
     path('invite-users/<uuid:room_id>/', views.invite_users, name='invite_users'),
    path('delete-room/<uuid:room_id>/', views.delete_room, name='delete_room'),
]

