from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
handler404 = "apps.core.views.error_404"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("users/", include("apps.users.urls")),
    path("friends/", include("apps.friends.urls")),
    path("chat/", include("apps.chat.urls")),
    path("groups/", include("apps.groups.urls")),
    path("posts/", include("apps.posts.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("calls/", include("apps.calls.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
