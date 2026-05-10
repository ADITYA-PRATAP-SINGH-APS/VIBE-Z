from django.urls import path
from apps.chat import consumers as chat_consumers
from apps.calls import consumers as call_consumers


websocket_urlpatterns = [
    path("ws/chat/<str:room_name>/", chat_consumers.ChatConsumer.as_asgi()),
    path("ws/calls/<str:room_name>/", call_consumers.CallConsumer.as_asgi()),
]
