from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from apps.users.models import User
from apps.groups.models import Group
from apps.groups.models import GroupMember
from apps.friends.models import Friendship
from apps.chat.models import Message
from apps.notifications.models import Notification
from apps.posts.models import Post
from .forms import ReportForm


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    friendships = Friendship.objects.filter(user1=request.user) | Friendship.objects.filter(user2=request.user)
    friend_count = friendships.count()
    group_count = GroupMember.objects.filter(user=request.user).count()
    post_count = Post.objects.filter(author=request.user, is_deleted=False).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    recent_messages = (
        Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
        .select_related("sender")
        .order_by("-created_at")[:5]
    )
    recent_groups = GroupMember.objects.filter(user=request.user).select_related("group").order_by("-joined_at")[:5]
    return render(
        request,
        "core/dashboard.html",
        {
            "friend_count": friend_count,
            "group_count": group_count,
            "post_count": post_count,
            "unread_notifications": unread_notifications,
            "recent_messages": recent_messages,
            "recent_groups": recent_groups,
        },
    )


def discover(request):
    users_qs = User.objects.all()
    if request.user.is_authenticated:
        users_qs = users_qs.exclude(pk=request.user.pk)
    users = users_qs.select_related("profile")[:12]

    groups = Group.objects.all()[:12]
    return render(request, "core/discover.html", {"users": users, "groups": groups})


def search(request):
    query = request.GET.get("q", "").strip()
    if query:
        users_qs = User.objects.filter(Q(unique_name__icontains=query) | Q(full_name__icontains=query))
        if request.user.is_authenticated:
            users_qs = users_qs.exclude(pk=request.user.pk)
        users = users_qs.select_related("profile").distinct().order_by("unique_name")[:50]
    else:
        users = User.objects.none()
    return render(request, "core/search.html", {"query": query, "users": users})


@login_required
def report(request):
    if request.method == "POST":
        form = ReportForm(request.POST, user=request.user)
        if form.is_valid():
            report_obj = form.save()
            from .services import enforce_report_thresholds

            enforce_report_thresholds(report_obj)
            messages.success(request, "Report submitted.")
        else:
            messages.error(request, "Report failed. Please add a reason.")
    return redirect(request.POST.get("next", "core:dashboard"))


def error_404(request, exception=None):
    return render(request, "core/error_404.html", status=404)
