from django.core.exceptions import ValidationError


def _validate_extension(file, allowed_extensions):
    if not hasattr(file, "name"):
        return
    ext = file.name.lower().rsplit(".", 1)[-1]
    if ext not in allowed_extensions:
        raise ValidationError("Unsupported file type.")


def validate_image_file(file):
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    allowed_ext = {"jpg", "jpeg", "png", "webp", "gif"}
    if hasattr(file, "content_type") and file.content_type:
        if file.content_type not in allowed_types:
            raise ValidationError("Only JPG, PNG, WEBP, or GIF images are allowed.")
    _validate_extension(file, allowed_ext)


def validate_media_file(file):
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "audio/mpeg",
        "audio/wav",
        "audio/webm",
        "audio/ogg",
        "video/mp4",
    }
    allowed_ext = {"jpg", "jpeg", "png", "webp", "gif", "mp3", "wav", "webm", "ogg", "mp4"}
    if hasattr(file, "content_type") and file.content_type:
        if file.content_type not in allowed_types:
            raise ValidationError("Unsupported media type.")
    _validate_extension(file, allowed_ext)
