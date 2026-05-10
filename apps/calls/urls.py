from django.urls import path
from . import views


app_name = "calls"

urlpatterns = [
    path("", views.call_screen, name="screen"),
    path("start/", views.start_call, name="start"),
    path("accept/<int:session_id>/", views.accept_call, name="accept"),
    path("decline/<int:session_id>/", views.decline_call, name="decline"),
    path("end/<int:session_id>/", views.end_call, name="end"),
]
