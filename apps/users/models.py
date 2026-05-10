from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models
from apps.core.validators import validate_image_file


class UserManager(BaseUserManager):
    def create_user(self, unique_name: str, password: str | None = None, **extra_fields):
        if not unique_name:
            raise ValueError("Users must have a unique name")
        unique_name = unique_name.strip()
        if len(unique_name) > 12:
            raise ValueError("Unique name must be 12 characters or fewer")
        email = extra_fields.get("email")
        if not email:
            raise ValueError("Users must have an email address")
        extra_fields["email"] = self.normalize_email(email)
        user = self.model(unique_name=unique_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, unique_name: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(unique_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    unique_name = models.CharField(
        max_length=12,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\S{1,12}$",
                message="Unique name must be up to 12 characters with no spaces.",
            )
        ],
        help_text="Used for login, search, mentions, and profile links.",
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    USERNAME_FIELD = "unique_name"
    REQUIRED_FIELDS = ["email", "full_name"]

    objects = UserManager()

    def __str__(self) -> str:
        return self.unique_name


class Profile(models.Model):
    THEME_CHOICES = [("dark", "Dark"), ("midnight", "Midnight"), ("sunset", "Sunset")]
    NOTIFY_CHOICES = [("all", "All"), ("mentions", "Mentions"), ("none", "None")]
    PRIVACY_CHOICES = [("public", "Public"), ("friends", "Friends"), ("private", "Private")]
    GENDER_CHOICES = [("male", "Male"), ("female", "Female"), ("other", "Other")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150, blank=True)
    age = models.PositiveSmallIntegerField(default=18, validators=[MinValueValidator(1), MaxValueValidator(120)])
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default="other")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, validators=[validate_image_file])
    theme_preference = models.CharField(max_length=20, choices=THEME_CHOICES, default="dark")
    notification_preference = models.CharField(max_length=20, choices=NOTIFY_CHOICES, default="all")
    privacy_setting = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default="public")

    def __str__(self) -> str:
        return f"{self.user.unique_name} profile"


class BlockList(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocker_set")
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_set")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blocker", "blocked")

    def __str__(self) -> str:
        return f"{self.blocker} blocked {self.blocked}"
