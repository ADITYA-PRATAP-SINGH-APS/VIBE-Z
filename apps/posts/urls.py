from django.urls import path
from . import views


app_name = "posts"

urlpatterns = [
    path("", views.feed, name="feed"),
    path("create/", views.create_post, name="create"),
    path("<int:post_id>/react/<str:reaction>/", views.react, name="react"),
    path("<int:post_id>/comment/", views.comment, name="comment"),
    path("<int:post_id>/save/", views.save_post, name="save"),
    path("<int:post_id>/share/", views.share_post, name="share"),
    path("<int:post_id>/delete/", views.delete_post, name="delete"),
]
