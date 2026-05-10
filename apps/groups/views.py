from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import GroupCreateForm, GroupUpdateForm
from .models import Group, GroupMember, GroupPin
from apps.notifications.models import Notification


def groups_list(request):
    query = request.GET.get("q", "").strip()
    if query:
        terms = [term for term in query.replace(",", " ").split() if term]
        search = Q()
        for term in terms:
            search |= Q(name__icontains=term)
            search |= Q(description__icontains=term)
            search |= Q(tags__icontains=term)
        groups = Group.objects.filter(search).distinct()
    else:
        groups = Group.objects.all()
    member_group_ids = set()
    if request.user.is_authenticated:
        member_group_ids = set(
            GroupMember.objects.filter(user=request.user).values_list("group_id", flat=True)
        )
    return render(
        request,
        "groups/list.html",
        {"groups": groups, "query": query, "member_group_ids": member_group_ids},
    )


def group_detail(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    members = group.memberships.select_related("user")
    is_member = False
    if request.user.is_authenticated:
        is_member = GroupMember.objects.filter(group=group, user=request.user).exists()
    update_form = GroupUpdateForm(instance=group) if request.user == group.admin else None
    return render(
        request,
        "groups/detail.html",
        {"group": group, "members": members, "update_form": update_form, "is_member": is_member},
    )


@login_required
def group_create(request):
    tag_suggestions = [
        "coding",
        "gaming",
        "travelling",
        "anime",
        "cricket",
        "football",
        "movies",
        "music",
        "startup",
        "business",
        "fitness",
        "gym",
        "books",
        "poetry",
        "memes",
        "photography",
        "editing",
        "design",
        "python",
        "webdev",
        "ai",
        "hacking",
        "stocks",
        "fashion",
        "food",
    ]
    if request.method == "POST":
        form = GroupCreateForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.admin = request.user
            group.save()
            GroupMember.objects.create(group=group, user=request.user, role="admin")
            return redirect("groups:detail", group_id=group.pk)
    else:
        form = GroupCreateForm()
    return render(request, "groups/create.html", {"form": form, "tag_suggestions": tag_suggestions})


@login_required
def join_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if group.public_join:
        GroupMember.objects.get_or_create(group=group, user=request.user)
        Notification.objects.create(
            user=group.admin,
            notification_type="group_join",
            text=f"{request.user.unique_name} joined {group.name}.",
        )
    return redirect("groups:detail", group_id=group.pk)


@login_required
def leave_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    GroupMember.objects.filter(group=group, user=request.user).delete()
    return redirect("groups:list")


@login_required
def pin_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    GroupPin.objects.get_or_create(user=request.user, group=group)
    return redirect("groups:detail", group_id=group.pk)


@login_required
def update_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id, admin=request.user)
    if request.method == "POST":
        form = GroupUpdateForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
    return redirect("groups:detail", group_id=group.pk)


@login_required
def unpin_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    GroupPin.objects.filter(user=request.user, group=group).delete()
    return redirect("groups:detail", group_id=group.pk)
