from django.urls import path
from . import views


app_name = "users"

urlpatterns = [
    path("profile/", views.profile_detail, name="profile"),
    path("profile/<str:unique_name>/", views.profile_detail, name="profile_detail"),
    path("settings/", views.settings_view, name="settings"),
    path("block/<str:unique_name>/", views.block_user, name="block"),
    path("unblock/<str:unique_name>/", views.unblock_user, name="unblock"),
]
