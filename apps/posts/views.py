from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import PostForm, CommentForm
from .models import Post, PostReaction, PostSave
from apps.notifications.models import Notification


@login_required
def feed(request):
    posts = (
        Post.objects.filter(is_deleted=False)
        .annotate(
            like_count=Count("reactions", filter=Q(reactions__reaction="like")),
            dislike_count=Count("reactions", filter=Q(reactions__reaction="dislike")),
        )
        .order_by("-created_at")
    )
    form = PostForm()
    return render(request, "posts/feed.html", {"posts": posts, "form": form})


@login_required
def create_post(request):
    cooldown = request.session.get("post_cooldown")
    if cooldown and cooldown > timezone.now().timestamp():
        return redirect("posts:feed")
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            request.session["post_cooldown"] = timezone.now().timestamp() + 10
    return redirect("posts:feed")


@login_required
def react(request, post_id, reaction):
    if request.method != "POST":
        return redirect("posts:feed")
    post = get_object_or_404(Post, pk=post_id)
    if reaction not in {"like", "dislike"}:
        return redirect("posts:feed")
    PostReaction.objects.update_or_create(post=post, user=request.user, defaults={"reaction": reaction})
    if post.author != request.user:
        Notification.objects.create(
            user=post.author,
            notification_type="post_like" if reaction == "like" else "post_dislike",
            text=f"{request.user.unique_name} {reaction}d your post.",
        )
    return redirect("posts:feed")


@login_required
def comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            if post.author != request.user:
                Notification.objects.create(
                    user=post.author,
                    notification_type="comment",
                    text=f"{request.user.unique_name} commented on your post.",
                )
    return redirect("posts:feed")


@login_required
def save_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    PostSave.objects.get_or_create(user=request.user, post=post)
    return redirect("posts:feed")


@login_required
def share_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    Post.objects.create(author=request.user, content=post.content, shared_from=post)
    return redirect("posts:feed")


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    post.is_deleted = True
    post.save(update_fields=["is_deleted"])
    return redirect("posts:feed")
