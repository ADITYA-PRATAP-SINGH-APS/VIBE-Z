from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProfileUpdateForm
from .models import User, BlockList
from apps.friends.models import FriendRequest, Friendship


def profile_detail(request, unique_name: str | None = None):
    if unique_name:
        profile_user = get_object_or_404(User, unique_name=unique_name)
    else:
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        profile_user = request.user

    mutual_friends = 0
    is_blocked = False
    is_blocked_by_other = False
    is_friend = False
    outgoing_request = None
    incoming_request = None
    dm_room = ""

    if request.user.is_authenticated and request.user != profile_user:
        # Mutual friends
        user_friends = set(
            Friendship.objects.filter(user1=request.user).values_list("user2_id", flat=True)
        ) | set(Friendship.objects.filter(user2=request.user).values_list("user1_id", flat=True))
        other_friends = set(
            Friendship.objects.filter(user1=profile_user).values_list("user2_id", flat=True)
        ) | set(Friendship.objects.filter(user2=profile_user).values_list("user1_id", flat=True))
        mutual_friends = len(user_friends & other_friends)

        # Block status (both directions)
        is_blocked = BlockList.objects.filter(blocker=request.user, blocked=profile_user).exists()
        is_blocked_by_other = BlockList.objects.filter(blocker=profile_user, blocked=request.user).exists()

        # Friendship status
        is_friend = Friendship.objects.filter(
            Q(user1=request.user, user2=profile_user) | Q(user1=profile_user, user2=request.user)
        ).exists()

        if is_friend:
            dm_room = f"dm-{min(profile_user.id, request.user.id)}-{max(profile_user.id, request.user.id)}"
        else:
            outgoing_request = FriendRequest.objects.filter(
                from_user=request.user, to_user=profile_user, status="pending"
            ).first()
            incoming_request = FriendRequest.objects.filter(
                from_user=profile_user, to_user=request.user, status="pending"
            ).first()

    return render(
        request,
        "users/profile.html",
        {
            "profile_user": profile_user,
            "mutual_friends": mutual_friends,
            "is_blocked": is_blocked,
            "is_blocked_by_other": is_blocked_by_other,
            "is_friend": is_friend,
            "outgoing_request": outgoing_request,
            "incoming_request": incoming_request,
            "dm_room": dm_room,
        },
    )


@login_required
def settings_view(request):
    profile = request.user.profile
    if request.method == "POST":
        if "change_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            form = ProfileUpdateForm(instance=profile)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                return redirect("users:settings")
        else:
            form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            password_form = PasswordChangeForm(request.user)
            if form.is_valid():
                form.save()
                return redirect("users:settings")
    else:
        form = ProfileUpdateForm(instance=profile)
        password_form = PasswordChangeForm(request.user)
    return render(
        request,
        "users/settings.html",
        {"form": form, "password_form": password_form},
    )


@login_required
def block_user(request, unique_name):
    target = get_object_or_404(User, unique_name=unique_name)
    if target != request.user:
        BlockList.objects.get_or_create(blocker=request.user, blocked=target)
    return redirect("users:profile_detail", unique_name=unique_name)


@login_required
def unblock_user(request, unique_name):
    target = get_object_or_404(User, unique_name=unique_name)
    BlockList.objects.filter(blocker=request.user, blocked=target).delete()
    return redirect("users:profile_detail", unique_name=unique_name)
