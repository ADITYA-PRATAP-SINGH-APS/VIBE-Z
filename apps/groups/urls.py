from django.urls import path
from . import views


app_name = "groups"

urlpatterns = [
    path("", views.groups_list, name="list"),
    path("<int:group_id>/", views.group_detail, name="detail"),
    path("create/", views.group_create, name="create"),
    path("<int:group_id>/join/", views.join_group, name="join"),
    path("<int:group_id>/leave/", views.leave_group, name="leave"),
    path("<int:group_id>/pin/", views.pin_group, name="pin"),
    path("<int:group_id>/unpin/", views.unpin_group, name="unpin"),
    path("<int:group_id>/update/", views.update_group, name="update"),
]
