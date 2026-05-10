import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.friends.models import Friendship
from apps.groups.models import Group, GroupMember
from apps.notifications.models import Notification
from apps.users.models import User

from .models import CallSession


def _broadcast_to_user(user_id: int, payload: dict) -> None:
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"call_user_{user_id}",
        {"type": "call_signal", "payload": payload},
    )


def _broadcast_to_room(room_name: str, payload: dict) -> None:
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"call_{room_name}",
        {"type": "call_signal", "payload": payload},
    )


@ensure_csrf_cookie
@login_required
def call_screen(request):
    friendships = Friendship.objects.filter(user1=request.user) | Friendship.objects.filter(user2=request.user)
    friend_ids = {
        item.user2_id if item.user1_id == request.user.id else item.user1_id for item in friendships
    }
    friends = User.objects.filter(id__in=friend_ids)
    groups = GroupMember.objects.filter(user=request.user).select_related("group")

    friend_rooms = [{"friend": friend} for friend in friends]
    group_rooms = [{"group": membership.group} for membership in groups]

    incoming_calls = (
        CallSession.objects.filter(callee=request.user, status="ringing")
        .select_related("caller")
        .order_by("-started_at")
    )
    call_history = (
        CallSession.objects.filter(Q(caller=request.user) | Q(callee=request.user))
        .select_related("caller", "callee")
        .order_by("-started_at")[:20]
    )

    selected_target = request.GET.get("target", "")
    selected_room = request.GET.get("room", "")
    selected_session = request.GET.get("session", "")
    selected_type = request.GET.get("type", "")
    selected_role = request.GET.get("role", "")
    auto_join = request.GET.get("auto", "")

    dial = request.GET.get("dial", "")
    dial_type = request.GET.get("dial_type", "")

    selected_target_user_id = ""
    selected_target_group_id = ""
    if selected_target.startswith("user:"):
        selected_target_user_id = selected_target.split("user:", 1)[1]
    elif selected_target.startswith("group:"):
        selected_target_group_id = selected_target.split("group:", 1)[1]

    return render(
        request,
        "calls/screen.html",
        {
            "friend_rooms": friend_rooms,
            "group_rooms": group_rooms,
            "incoming_calls": incoming_calls,
            "call_history": call_history,
            "selected_target": selected_target,
            "selected_target_user_id": selected_target_user_id,
            "selected_target_group_id": selected_target_group_id,
            "selected_room": selected_room,
            "selected_session": selected_session,
            "selected_type": selected_type,
            "selected_role": selected_role,
            "auto_join": auto_join,
            "dial": dial,
            "dial_type": dial_type,
        },
    )


@login_required
def start_call(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid request"}, status=400)

    target = request.POST.get("target", "")
    call_type = request.POST.get("call_type", "audio")
    room_name = f"call-{uuid.uuid4().hex}"

    if target.startswith("user:"):
        user_id = target.split("user:", 1)[1]
        callee = get_object_or_404(User, pk=user_id)

        if callee.id == request.user.id:
            return JsonResponse({"ok": False, "error": "You can't call yourself"}, status=400)

        is_friend = Friendship.objects.filter(
            Q(user1=request.user, user2=callee) | Q(user1=callee, user2=request.user)
        ).exists()
        if not is_friend:
            return HttpResponseForbidden("Not allowed")

        session = CallSession.objects.create(
            caller=request.user,
            callee=callee,
            call_type="video" if call_type == "video" else "audio",
            status="ringing",
            room_name=room_name,
        )

        Notification.objects.create(
            user=callee,
            notification_type="call",
            text=f"{request.user.unique_name} is calling you.",
        )

        payload = {
            "event": "incoming_call",
            "session_id": session.id,
            "room": session.room_name,
            "call_type": session.call_type,
            "caller": {"id": request.user.id, "unique_name": request.user.unique_name},
            "callee": {"id": callee.id, "unique_name": callee.unique_name},
        }
        _broadcast_to_user(callee.id, payload)

        return JsonResponse(
            {
                "ok": True,
                "session_id": session.id,
                "room": session.room_name,
                "call_type": session.call_type,
                "callee": {"id": callee.id, "unique_name": callee.unique_name},
            }
        )

    if target.startswith("group:"):
        group_id = target.split("group:", 1)[1]
        group = get_object_or_404(Group, pk=group_id)
        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return HttpResponseForbidden("Not allowed")

        session = CallSession.objects.create(
            caller=request.user,
            group=group,
            call_type="group",
            status="ringing",
            room_name=room_name,
        )
        return JsonResponse({"ok": True, "session_id": session.id, "room": session.room_name, "call_type": session.call_type})

    return JsonResponse({"ok": False, "error": "Select a target"}, status=400)


@login_required
def accept_call(request, session_id: int):
    if request.method != "POST":
        return redirect("calls:screen")

    session = get_object_or_404(CallSession, pk=session_id, callee=request.user)
    if session.status == "ended":
        return redirect("calls:screen")

    session.status = "active"
    session.save(update_fields=["status"])

    payload = {
        "event": "call_accepted",
        "session_id": session.id,
        "room": session.room_name,
        "call_type": session.call_type,
    }
    _broadcast_to_user(session.caller_id, payload)
    _broadcast_to_room(session.room_name, payload)

    # Include target so the call screen can label the remote pane (Buddy/Gang)
    redirect_url = (
        f"/calls/?room={session.room_name}&session={session.id}&type={session.call_type}"
        f"&role=callee&auto=1&target=user:{session.caller_id}"
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, **payload, "redirect": redirect_url})
    return redirect(redirect_url)


@login_required
def decline_call(request, session_id: int):
    if request.method != "POST":
        return redirect("calls:screen")

    session = get_object_or_404(CallSession, pk=session_id, callee=request.user)
    if session.status != "ended":
        session.status = "ended"
        session.ended_at = timezone.now()
        session.save(update_fields=["status", "ended_at"])

    payload = {"event": "call_declined", "session_id": session.id, "room": session.room_name}
    _broadcast_to_user(session.caller_id, payload)
    _broadcast_to_room(session.room_name, payload)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, **payload})
    return redirect("calls:screen")


@login_required
def end_call(request, session_id: int):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid request"}, status=400)

    session = get_object_or_404(CallSession, pk=session_id)
    if request.user.id not in {session.caller_id, session.callee_id}:
        return HttpResponseForbidden("Not allowed")

    if session.status != "ended":
        session.status = "ended"
        session.ended_at = timezone.now()
        session.save(update_fields=["status", "ended_at"])

    payload = {"event": "hangup", "session_id": session.id, "room": session.room_name}
    _broadcast_to_room(session.room_name, payload)
    if session.caller_id:
        _broadcast_to_user(session.caller_id, payload)
    if session.callee_id:
        _broadcast_to_user(session.callee_id, payload)

    return JsonResponse({"ok": True})
