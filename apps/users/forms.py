from django import forms
from django.contrib.auth import get_user_model
from .models import Profile


User = get_user_model()


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "display_name",
            "age",
            "gender",
            "bio",
            "avatar",
            "theme_preference",
            "notification_preference",
            "privacy_setting",
        ]


class UserSearchForm(forms.Form):
    query = forms.CharField(required=False)
