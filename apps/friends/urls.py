from django.urls import path
from . import views


app_name = "friends"

urlpatterns = [
    path("", views.friends_list, name="list"),
    path("request/<str:unique_name>/", views.send_request, name="send_request"),
    path("accept/<int:request_id>/", views.accept_request, name="accept_request"),
    path("reject/<int:request_id>/", views.reject_request, name="reject_request"),
    path("remove/<str:unique_name>/", views.remove_friend, name="remove_friend"),
]
