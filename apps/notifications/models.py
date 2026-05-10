from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ("friend_request", "Friend Request"),
        ("friend_accept", "Friend Accepted"),
        ("message", "New Message"),
        ("group_join", "Group Join"),
        ("post_like", "Post Like"),
        ("post_dislike", "Post Dislike"),
        ("comment", "Comment"),
        ("mention", "Mention"),
        ("call", "Call"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    text = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.notification_type} for {self.user}"
