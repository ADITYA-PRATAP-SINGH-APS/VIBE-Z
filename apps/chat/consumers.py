import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.groups.models import Group, GroupMember
from apps.users.models import User
from .models import Message, Poll, PollOption


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        allowed = await self._user_allowed_room(user)
        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        data = json.loads(text_data)
        event = data.get("event", "message")

        sender = data.get("sender", "Anonymous")
        if self.scope["user"].is_authenticated:
            sender = self.scope["user"].unique_name

        if event == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "typing_indicator", "sender": sender},
            )
            return

        if event == "poll_create":
            if not self.scope["user"].is_authenticated:
                return
            question = (data.get("question") or "").strip()
            options = data.get("options") or []
            if not isinstance(options, list):
                return
            options = [str(o).strip() for o in options]
            options = [o for o in options if o][:6]
            if not question or len(options) < 2:
                return

            payload = await self._create_poll(self.scope["user"], question, options)
            if payload.get("event") == "error":
                await self.send(text_data=json.dumps(payload))
                return
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", **payload},
            )
            return

        # Default: normal text message
        message = (data.get("message") or "").strip()
        reply_to_id = data.get("reply_to_id")
        if not message:
            return

        if self.scope["user"].is_authenticated:
            payload = await self._create_message(self.scope["user"], message, reply_to_id)
            if payload.get("event") == "error":
                await self.send(text_data=json.dumps(payload))
                return
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", **payload},
            )
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "event": "message", "message": message, "sender": sender},
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({"event": "typing", "sender": event["sender"]}))

    @database_sync_to_async
    def _user_allowed_room(self, user) -> bool:
        if str(self.room_name).isdigit():
            group = Group.objects.filter(pk=int(self.room_name)).first()
            if not group:
                return False
            return GroupMember.objects.filter(group=group, user=user).exists()

        if str(self.room_name).startswith("dm-"):
            parts = str(self.room_name).split("-")
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
                return False
            user_ids = {int(parts[1]), int(parts[2])}
            return user.id in user_ids

        return False

    @database_sync_to_async
    def _create_message(self, user, message, reply_to_id):
        group = None
        recipient = None
        if str(self.room_name).isdigit():
            group = Group.objects.filter(pk=int(self.room_name)).first()
            if not group or not GroupMember.objects.filter(group=group, user=user).exists():
                return {"event": "error", "error": "Not allowed"}
        elif str(self.room_name).startswith("dm-"):
            parts = str(self.room_name).split("-")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                user_ids = {int(parts[1]), int(parts[2])}
                if user.id in user_ids:
                    other_id = (user_ids - {user.id}).pop()
                    recipient = User.objects.filter(pk=other_id).first()
                else:
                    return {"event": "error", "error": "Not allowed"}
        reply_to = Message.objects.filter(pk=reply_to_id).first() if reply_to_id else None
        if str(self.room_name).startswith("dm-") and recipient is None:
            return {"event": "error", "error": "Not allowed"}

        msg = Message.objects.create(
            sender=user, group=group, recipient=recipient, content=message, reply_to=reply_to
        )
        payload = {
            "event": "message",
            "message": msg.content,
            "sender": user.unique_name,
            "message_id": msg.id,
        }
        if msg.reply_to:
            payload["reply_to"] = {
                "id": msg.reply_to_id,
                "sender": msg.reply_to.sender.unique_name,
                "content": msg.reply_to.content,
            }
        return payload

    @database_sync_to_async
    def _create_poll(self, user, question: str, options: list[str]):
        group = None
        recipient = None
        if str(self.room_name).isdigit():
            group = Group.objects.filter(pk=int(self.room_name)).first()
            if not group or not GroupMember.objects.filter(group=group, user=user).exists():
                return {"event": "error", "error": "Not allowed"}
        elif str(self.room_name).startswith("dm-"):
            parts = str(self.room_name).split("-")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                user_ids = {int(parts[1]), int(parts[2])}
                if user.id in user_ids:
                    other_id = (user_ids - {user.id}).pop()
                    recipient = User.objects.filter(pk=other_id).first()
                else:
                    return {"event": "error", "error": "Not allowed"}

        if str(self.room_name).startswith("dm-") and recipient is None:
            return {"event": "error", "error": "Not allowed"}

        msg = Message.objects.create(sender=user, group=group, recipient=recipient, content="")
        poll = Poll.objects.create(message=msg, question=question)
        option_objs = [PollOption.objects.create(poll=poll, text=o) for o in options]

        return {
            "event": "poll",
            "sender": user.unique_name,
            "message_id": msg.id,
            "poll": {
                "id": poll.id,
                "question": poll.question,
                "options": [{"id": opt.id, "text": opt.text, "votes": opt.votes_count} for opt in option_objs],
            },
        }
