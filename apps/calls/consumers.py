import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.groups.models import GroupMember
from .models import CallSession


class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.raw_room_name = self.scope["url_route"]["kwargs"]["room_name"]
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close()
            return

        # Personal channel for incoming call alerts: ws/calls/u-<user_id>/
        if str(self.raw_room_name).startswith("u-") and str(self.raw_room_name)[2:].isdigit():
            uid = int(str(self.raw_room_name)[2:])
            if uid != user.id:
                await self.close()
                return
            self.room_group_name = f"call_user_{uid}"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            return

        # Call room signaling channel: ws/calls/<room_name>/
        allowed = await self._user_allowed_call_room(user.id, str(self.raw_room_name))
        if not allowed:
            await self.close()
            return

        self.room_group_name = f"call_{self.raw_room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if getattr(self, "room_group_name", None):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "call_signal", "payload": data},
        )

    async def call_signal(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _user_allowed_call_room(self, user_id: int, room_name: str) -> bool:
        session = (
            CallSession.objects.filter(room_name=room_name)
            .select_related("caller", "callee", "group")
            .first()
        )
        if not session:
            return False
        if session.status == "ended":
            return False
        if session.caller_id == user_id or session.callee_id == user_id:
            return True
        if session.group_id:
            return GroupMember.objects.filter(group_id=session.group_id, user_id=user_id).exists()
        return False
