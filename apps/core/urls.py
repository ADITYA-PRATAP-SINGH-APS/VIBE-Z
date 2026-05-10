from django.urls import path
from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("discover/", views.discover, name="discover"),
    path("search/", views.search, name="search"),
    path("report/", views.report, name="report"),
]
