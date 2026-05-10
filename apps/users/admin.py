from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, BlockList


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["unique_name"]
    list_display = ["unique_name", "email", "full_name", "is_staff", "is_active"]
    fieldsets = (
        (None, {"fields": ("unique_name", "password")}),
        ("Personal info", {"fields": ("full_name", "email")}),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "last_seen")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("unique_name", "email", "full_name", "password1", "password2"),
            },
        ),
    )
    search_fields = ["unique_name", "email", "full_name"]


admin.site.register(Profile)
admin.site.register(BlockList)
