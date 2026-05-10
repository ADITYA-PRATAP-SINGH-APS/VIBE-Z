def notifications_count(request):
    if request.user.is_authenticated and hasattr(request.user, "notifications"):
        profile = getattr(request.user, "profile", None)
        if profile and profile.notification_preference == "none":
            return {"notifications_count": 0}
        return {"notifications_count": request.user.notifications.filter(is_read=False).count()}
    return {"notifications_count": 0}
