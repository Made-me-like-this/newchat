from . import views
from django.urls import path

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('chat_list/', views.chat_list, name='chat_list'),
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('send-message/', views.send_message, name='send_message'),
    path('chat/create/', views.create_chat, name='create_chat'),
    path('chat/<int:chat_id>/messages/load/', views.load_more_messages, name='load_more_messages'),
    path('room/', views.chat_area, name='chat_area'),
    path('logout/', views.logout, name='logout')
]
