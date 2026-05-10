from django.conf import settings
from django.db import models
from apps.groups.models import Group


class CallSession(models.Model):
    CALL_CHOICES = [("audio", "Audio"), ("video", "Video"), ("group", "Group Voice")]
    STATUS_CHOICES = [("ringing", "Ringing"), ("active", "Active"), ("ended", "Ended")]
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="calls_started")
    callee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="calls_received"
    )
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="call_sessions")
    call_type = models.CharField(max_length=20, choices=CALL_CHOICES, default="audio")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ringing")
    room_name = models.CharField(max_length=120, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.call_type} call {self.room_name}"
