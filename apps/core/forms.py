from django import forms
from django.core.exceptions import ValidationError
from .models import Report


class ReportForm(forms.ModelForm):
    next = forms.CharField(required=False)

    class Meta:
        model = Report
        fields = ["target_user", "target_post_id", "reason"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["target_user"].required = False
        self.fields["target_post_id"].required = False
        self.fields["reason"].required = True

    def clean(self):
        cleaned = super().clean()

        target_user = cleaned.get("target_user")
        target_post_id = cleaned.get("target_post_id")

        if not target_user and not target_post_id:
            raise ValidationError("Select a user or post to report.")

        if target_user and target_user == self.user:
            raise ValidationError("You cannot report yourself.")

        reason = cleaned.get("reason", "").strip()
        if not reason:
            raise ValidationError("Please provide a reason for the report.")

        return cleaned

    def save(self, commit=True):
        report = super().save(commit=False)
        report.reporter = self.user
        if commit:
            report.save()
        return report
