from django.urls import path
from . import views


app_name = "chat"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("room/<str:room_name>/", views.room, name="room"),
    path("room/<str:room_name>/message/", views.send_message, name="send_message"),
    path("room/<str:room_name>/media/", views.send_media, name="send_media"),
    path("room/<str:room_name>/poll/", views.create_poll, name="create_poll"),
    path("poll/<int:poll_id>/vote/", views.vote_poll, name="vote_poll"),
    path("message/<int:message_id>/delete/", views.delete_message, name="delete_message"),
]
