from django.urls import path
from .views import ChatMessageListView, ChatMessageCreateView
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("messages/", ChatMessageListView.as_view(), name="chat-messages"),
    path("messages/create/", ChatMessageCreateView.as_view(), name="chat-create"),
]
