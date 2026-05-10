from django.contrib import admin

from .models import Report
from .services import enforce_report_thresholds


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "target_user", "target_post_id", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reporter__unique_name", "target_user__unique_name", "reason")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ensure thresholds are enforced even when reports are created in admin.
        enforce_report_thresholds(obj)
