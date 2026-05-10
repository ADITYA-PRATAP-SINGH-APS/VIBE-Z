from django.conf import settings
from django.db import models
from apps.core.validators import validate_media_file
from apps.groups.models import Group


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages_sent")
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages_received"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name="messages")
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    reply_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies")

    def __str__(self) -> str:
        return f"Message from {self.sender}"


class MessageMedia(models.Model):
    MEDIA_CHOICES = [("image", "Image"), ("audio", "Audio"), ("video", "Video")]
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="media")
    media_file = models.FileField(upload_to="chat_media/", validators=[validate_media_file])
    media_type = models.CharField(max_length=20, choices=MEDIA_CHOICES)

    def __str__(self) -> str:
        return f"{self.media_type} for {self.message_id}"


class Poll(models.Model):
    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name="poll")
    question = models.CharField(max_length=200)

    def __str__(self) -> str:
        return f"Poll {self.pk}"


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=120)
    votes_count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"Option {self.pk} for poll {self.poll_id}"


class PollVote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="poll_votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("poll", "voter")

    def __str__(self) -> str:
        return f"Vote {self.pk} on poll {self.poll_id}"
