from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from apps.users.models import User, BlockList
from .models import FriendRequest, Friendship
from apps.notifications.models import Notification


@login_required
def friends_list(request):
    friendships = Friendship.objects.filter(user1=request.user) | Friendship.objects.filter(user2=request.user)
    friendships = friendships.select_related("user1", "user2").order_by("-created_at")
    friend_ids = {
        friend.user2_id if friend.user1_id == request.user.id else friend.user1_id
        for friend in friendships
    }
    friends = User.objects.filter(id__in=friend_ids)
    friend_rooms = [
        {"friend": friend, "room": f"dm-{min(friend.id, request.user.id)}-{max(friend.id, request.user.id)}"}
        for friend in friends
    ]
    incoming_requests = FriendRequest.objects.filter(to_user=request.user, status="pending").select_related(
        "from_user"
    )
    outgoing_requests = FriendRequest.objects.filter(from_user=request.user, status="pending").select_related(
        "to_user"
    )
    activity = friendships[:5]
    return render(
        request,
        "friends/list.html",
        {
            "friends": friends,
            "friend_rooms": friend_rooms,
            "incoming_requests": incoming_requests,
            "outgoing_requests": outgoing_requests,
            "activity": activity,
        },
    )


@login_required
def send_request(request, unique_name):
    if request.method != "POST":
        return redirect("friends:list")
    target = get_object_or_404(User, unique_name=unique_name)
    if target == request.user:
        return redirect("friends:list")
    if BlockList.objects.filter(blocker=target, blocked=request.user).exists():
        return redirect("friends:list")
    if BlockList.objects.filter(blocker=request.user, blocked=target).exists():
        return redirect("friends:list")
    if Friendship.objects.filter(user1=request.user, user2=target).exists() or Friendship.objects.filter(
        user1=target, user2=request.user
    ).exists():
        return redirect("friends:list")
    request_obj, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=target)
    if created:
        Notification.objects.create(
            user=target,
            notification_type="friend_request",
            text=f"{request.user.unique_name} sent you a friend request.",
        )
    return redirect("friends:list")


@login_required
def accept_request(request, request_id):
    if request.method != "POST":
        return redirect("friends:list")
    friend_request = get_object_or_404(FriendRequest, pk=request_id, to_user=request.user)
    friend_request.status = "accepted"
    friend_request.save(update_fields=["status"])
    Friendship.objects.get_or_create(user1=friend_request.from_user, user2=friend_request.to_user)
    Notification.objects.create(
        user=friend_request.from_user,
        notification_type="friend_accept",
        text=f"{request.user.unique_name} accepted your friend request.",
    )
    return redirect("friends:list")


@login_required
def reject_request(request, request_id):
    if request.method != "POST":
        return redirect("friends:list")
    friend_request = get_object_or_404(FriendRequest, pk=request_id, to_user=request.user)
    friend_request.status = "rejected"
    friend_request.save(update_fields=["status"])
    return redirect("friends:list")


@login_required
def remove_friend(request, unique_name):
    if request.method != "POST":
        return redirect("friends:list")
    target = get_object_or_404(User, unique_name=unique_name)
    Friendship.objects.filter(user1=request.user, user2=target).delete()
    Friendship.objects.filter(user1=target, user2=request.user).delete()
    return redirect("friends:list")
