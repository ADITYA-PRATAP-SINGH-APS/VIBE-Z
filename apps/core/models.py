from django.conf import settings
from django.db import models


class Report(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("reviewed", "Reviewed"), ("closed", "Closed")]

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_made")
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports_received"
    )
    target_post_id = models.PositiveIntegerField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Report #{self.pk} by {self.reporter}"
