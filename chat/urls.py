from django.urls import path
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from .views import (
    LoginView, LogoutView, RegisterView, HomeView, RoomView, CreateRoomView,
    MessageListView, ProfileView, ProfileEditView, VideoListView, VideoUploadView,
    VideoDetailView, FriendListView, SendFriendRequestView, AcceptFriendRequestView,
    ActiveUsersView, VideoCommentView, VideoReactionView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('', HomeView.as_view(), name='home'),
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
]
