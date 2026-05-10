from django.conf import settings
from django.db import models
from apps.core.validators import validate_image_file


class Group(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField()
    display_picture = models.ImageField(upload_to="group_dps/", blank=True, null=True, validators=[validate_image_file])
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="groups_administered")
    tags = models.TextField(help_text="Comma-separated keywords/tags.")
    public_join = models.BooleanField(default=True)
    rules = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.tags:
            items = [tag.strip().lower() for tag in self.tags.split(",")]
            items = [tag for tag in items if tag]
            self.tags = ",".join(dict.fromkeys(items))
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class GroupMember(models.Model):
    ROLE_CHOICES = [("member", "Member"), ("moderator", "Moderator"), ("admin", "Admin")]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self) -> str:
        return f"{self.user} in {self.group}"


class GroupPin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pinned_groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="pins")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "group")

    def __str__(self) -> str:
        return f"{self.user} pinned {self.group}"
