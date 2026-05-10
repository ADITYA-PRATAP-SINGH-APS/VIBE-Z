from django import forms
from .models import Group


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "description", "display_picture", "tags", "public_join", "rules"]


class GroupUpdateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["description", "display_picture", "rules", "tags", "public_join"]
