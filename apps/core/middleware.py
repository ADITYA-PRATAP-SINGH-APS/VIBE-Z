from django.utils import timezone


class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            last = request.session.get("last_seen_update")
            if not last or now.timestamp() - last > 60:
                request.user.last_seen = now
                request.user.is_online = True
                request.user.save(update_fields=["last_seen", "is_online"])
                request.session["last_seen_update"] = now.timestamp()
        return self.get_response(request)
