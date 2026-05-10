from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q, Exists, OuterRef
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.groups.models import GroupMember, Group
from apps.friends.models import Friendship
from apps.users.models import User
from .models import Message, MessageMedia, Poll, PollOption, PollVote


@login_required
def inbox(request):
    memberships = GroupMember.objects.filter(user=request.user).select_related("group")
    friendships = Friendship.objects.filter(user1=request.user) | Friendship.objects.filter(user2=request.user)
    friend_ids = {
        item.user2_id if item.user1_id == request.user.id else item.user1_id for item in friendships
    }
    friends = User.objects.filter(id__in=friend_ids)
    dm_rooms = [
        {
            "friend": friend,
            "room": f"dm-{min(friend.id, request.user.id)}-{max(friend.id, request.user.id)}",
        }
        for friend in friends
    ]
    recent_messages = (
        Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
        .annotate(
            has_audio=Exists(
                MessageMedia.objects.filter(message=OuterRef("pk"), media_type="audio")
            ),
            has_media=Exists(MessageMedia.objects.filter(message=OuterRef("pk"))),
        )
        .select_related("sender")
        .order_by("-created_at")[:5]
    )
    return render(
        request,
        "chat/inbox.html",
        {
            "memberships": memberships,
            "recent_messages": recent_messages,
            "dm_rooms": dm_rooms,
        },
    )


def _room_name_for_message(message: Message) -> str:
    if message.group_id:
        return str(message.group_id)
    if message.recipient_id:
        a = min(message.sender_id, message.recipient_id)
        b = max(message.sender_id, message.recipient_id)
        return f"dm-{a}-{b}"
    return "unknown"


def _user_can_access_message(user: User, message: Message) -> bool:
    if message.group_id:
        return GroupMember.objects.filter(group_id=message.group_id, user=user).exists()
    if message.recipient_id:
        return user.id in {message.sender_id, message.recipient_id}
    return False


def _broadcast_to_room(message: Message, payload: dict) -> None:
    room_name = _room_name_for_message(message)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_name}",
        {"type": "chat_message", **payload},
    )


@login_required
def room(request, room_name: str):
    group = None
    recipient = None
    chat_messages = Message.objects.none()
    if room_name.isdigit():
        group = Group.objects.filter(pk=int(room_name)).first()
        if not group:
            return redirect("chat:inbox")
        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return redirect("chat:inbox")
        chat_messages = Message.objects.filter(group=group).order_by("created_at")
        chat_messages.exclude(sender=request.user).update(is_seen=True)
    elif room_name.startswith("dm-"):
        parts = room_name.split("-")
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            user_ids = {int(parts[1]), int(parts[2])}
            if request.user.id in user_ids:
                other_id = (user_ids - {request.user.id}).pop()
                recipient = User.objects.filter(pk=other_id).first()
                chat_messages = Message.objects.filter(
                    sender=request.user, recipient=recipient
                ) | Message.objects.filter(sender=recipient, recipient=request.user)
                chat_messages = chat_messages.order_by("created_at")
                chat_messages.filter(recipient=request.user).update(is_seen=True)
            else:
                return redirect("chat:inbox")
        else:
            return redirect("chat:inbox")

    chat_messages = chat_messages.select_related(
        "sender",
        "sender__profile",
        "reply_to",
        "reply_to__sender",
        "poll",
    ).prefetch_related("media", "poll__options")

    return render(
        request,
        "chat/room.html",
        {
            "room_name": room_name,
            "chat_messages": chat_messages,
            "group": group,
            "recipient": recipient,
        },
    )


@login_required
def send_media(request, room_name: str):
    if request.method == "POST":
        group = None
        recipient = None
        if room_name.isdigit():
            group = Group.objects.filter(pk=int(room_name)).first()
            if not group:
                return redirect("chat:inbox")
            if not GroupMember.objects.filter(group=group, user=request.user).exists():
                return HttpResponseForbidden("Not allowed")
        elif room_name.startswith("dm-"):
            parts = room_name.split("-")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                user_ids = {int(parts[1]), int(parts[2])}
                if request.user.id in user_ids:
                    other_id = (user_ids - {request.user.id}).pop()
                    recipient = User.objects.filter(pk=other_id).first()

        content = request.POST.get("content", "")
        media_file = request.FILES.get("media_file")
        if not media_file and not content:
            return redirect("chat:room", room_name=room_name)

        if room_name.startswith("dm-") and recipient is None:
            return HttpResponseForbidden("Not allowed")

        message = Message.objects.create(
            sender=request.user, group=group, recipient=recipient, content=content
        )

        media_payload = []
        if media_file:
            content_type = media_file.content_type or ""
            if content_type.startswith("image"):
                media_type = "image"
            elif content_type.startswith("audio"):
                media_type = "audio"
            elif content_type.startswith("video"):
                media_type = "video"
            else:
                media_type = "image"
            media_obj = MessageMedia.objects.create(message=message, media_file=media_file, media_type=media_type)
            media_payload.append({"type": media_obj.media_type, "url": media_obj.media_file.url})

        payload = {
            "event": "media",
            "sender": request.user.unique_name,
            "message_id": message.id,
            "caption": message.content,
            "media": media_payload,
        }
        _broadcast_to_room(message, payload)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(payload)

    return redirect("chat:room", room_name=room_name)


@login_required
def send_message(request, room_name: str):
    if request.method == "POST":
        group = None
        recipient = None
        if room_name.isdigit():
            group = Group.objects.filter(pk=int(room_name)).first()
            if not group:
                return redirect("chat:inbox")
            if not GroupMember.objects.filter(group=group, user=request.user).exists():
                return HttpResponseForbidden("Not allowed")
        elif room_name.startswith("dm-"):
            parts = room_name.split("-")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                user_ids = {int(parts[1]), int(parts[2])}
                if request.user.id in user_ids:
                    other_id = (user_ids - {request.user.id}).pop()
                    recipient = User.objects.filter(pk=other_id).first()
        content = request.POST.get("content", "").strip()
        if not content:
            return redirect("chat:room", room_name=room_name)
        reply_to_id = request.POST.get("reply_to_id")
        reply_to = Message.objects.filter(pk=reply_to_id).first() if reply_to_id else None
        if room_name.startswith("dm-") and recipient is None:
            return HttpResponseForbidden("Not allowed")

        message = Message.objects.create(
            sender=request.user,
            group=group,
            recipient=recipient,
            content=content,
            reply_to=reply_to,
        )
    return redirect("chat:room", room_name=room_name)


@login_required
def create_poll(request, room_name: str):
    if request.method != "POST":
        return redirect("chat:room", room_name=room_name)

    group = None
    recipient = None
    if room_name.isdigit():
        group = Group.objects.filter(pk=int(room_name)).first()
        if not group:
            return redirect("chat:inbox")
        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return HttpResponseForbidden("Not allowed")
    elif room_name.startswith("dm-"):
        parts = room_name.split("-")
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            user_ids = {int(parts[1]), int(parts[2])}
            if request.user.id in user_ids:
                other_id = (user_ids - {request.user.id}).pop()
                recipient = User.objects.filter(pk=other_id).first()

    question = (request.POST.get("question") or "").strip()
    options = [(request.POST.get(f"option_{i}") or "").strip() for i in range(1, 7)]
    options = [o for o in options if o]

    if not question or len(options) < 2:
        return redirect("chat:room", room_name=room_name)

    if room_name.startswith("dm-") and recipient is None:
        return HttpResponseForbidden("Not allowed")

    message = Message.objects.create(sender=request.user, group=group, recipient=recipient, content="")
    poll = Poll.objects.create(message=message, question=question)
    option_objs = [PollOption.objects.create(poll=poll, text=o) for o in options]

    payload = {
        "event": "poll",
        "sender": request.user.unique_name,
        "message_id": message.id,
        "poll": {
            "id": poll.id,
            "question": poll.question,
            "options": [{"id": opt.id, "text": opt.text, "votes": opt.votes_count} for opt in option_objs],
        },
    }
    _broadcast_to_room(message, payload)

    return redirect("chat:room", room_name=room_name)


@login_required
def vote_poll(request, poll_id: int):
    poll = get_object_or_404(Poll.objects.select_related("message"), pk=poll_id)
    message = poll.message
    if not _user_can_access_message(request.user, message):
        return HttpResponseForbidden("Not allowed")

    if request.method != "POST":
        return redirect("chat:room", room_name=_room_name_for_message(message))

    option_id = request.POST.get("option_id")
    option = PollOption.objects.filter(pk=option_id, poll=poll).first()
    if not option:
        return JsonResponse({"ok": False, "error": "Invalid option"}, status=400)

    with transaction.atomic():
        existing = PollVote.objects.select_for_update().filter(poll=poll, voter=request.user).first()
        if existing and existing.option_id == option.id:
            pass
        else:
            if existing:
                PollOption.objects.filter(pk=existing.option_id).update(votes_count=F("votes_count") - 1)
                existing.option = option
                existing.save(update_fields=["option"])
            else:
                PollVote.objects.create(poll=poll, option=option, voter=request.user)
            PollOption.objects.filter(pk=option.id).update(votes_count=F("votes_count") + 1)

    options = list(PollOption.objects.filter(poll=poll).values("id", "text", "votes_count"))
    payload = {
        "event": "poll_update",
        "poll": {
            "id": poll.id,
            "options": [{"id": o["id"], "text": o["text"], "votes": o["votes_count"]} for o in options],
        },
    }
    _broadcast_to_room(message, payload)

    return JsonResponse({"ok": True, **payload})


@login_required
def delete_message(request, message_id: int):
    message = get_object_or_404(Message, pk=message_id, sender=request.user)
    message.is_deleted = True
    message.save(update_fields=["is_deleted"])
    if message.group_id:
        return redirect("chat:room", room_name=message.group_id)
    return redirect("chat:inbox")
