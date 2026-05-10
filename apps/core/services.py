from __future__ import annotations

from django.db import transaction

from .models import Report


def enforce_report_thresholds(report: Report) -> None:
    """Enforce automatic actions based on reports.

    Rules:
    - Ban (deactivate) a user after 3+ reports from *unique* reporters.
    - Remove (soft-delete) a post after 100+ reports from *unique* reporters.

    Notes:
    - We ignore reports with status='closed'.
    - Uses row locks to reduce race conditions under concurrent reporting.
    """

    if report.target_user_id:
        from apps.users.models import User

        with transaction.atomic():
            try:
                target_user = User.objects.select_for_update().get(pk=report.target_user_id)
            except User.DoesNotExist:
                target_user = None

            if target_user and target_user.is_active:
                unique_reporters = (
                    Report.objects.filter(target_user_id=target_user.pk)
                    .exclude(status="closed")
                    .values("reporter_id")
                    .distinct()
                    .count()
                )
                if unique_reporters >= 3:
                    target_user.is_active = False
                    target_user.save(update_fields=["is_active"])

    if report.target_post_id:
        from apps.posts.models import Post

        with transaction.atomic():
            try:
                post = Post.objects.select_for_update().get(pk=report.target_post_id)
            except Post.DoesNotExist:
                post = None

            if post and not post.is_deleted:
                unique_reporters = (
                    Report.objects.filter(target_post_id=post.pk)
                    .exclude(status="closed")
                    .values("reporter_id")
                    .distinct()
                    .count()
                )
                if unique_reporters >= 100:
                    post.is_deleted = True
                    post.save(update_fields=["is_deleted"])
